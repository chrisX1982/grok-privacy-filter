# Tests: Hook + Proxy allow/deny + health
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Write-Host "Repo: $RepoRoot"

$fail = 0

# --- Hook unit ---
$code = @'
import json, subprocess, sys
from pathlib import Path
root = Path(sys.argv[1])
script = root / "hooks" / "block-xai-upload.py"
cases = [
  ("deny curl", {"toolName":"run_terminal_command","toolInput":{"command":"curl -X POST https://cli-chat-proxy.grok.com/v1/storage -d x"}}, "deny"),
  ("allow git", {"toolName":"run_terminal_command","toolInput":{"command":"git status"}}, "allow"),
  ("deny fetch", {"toolName":"web_fetch","toolInput":{"url":"https://x.ai/"}}, "deny"),
  ("allow read", {"toolName":"read_file","toolInput":{"target_file":"a.py"}}, "allow"),
]
fail = 0
for name, payload, expect in cases:
  p = subprocess.run([sys.executable, str(script)], input=json.dumps(payload), text=True, capture_output=True)
  d = json.loads(p.stdout.strip()).get("decision")
  ok = d == expect
  print(("OK" if ok else "FAIL"), name, "got", d)
  fail += 0 if ok else 1
sys.exit(fail)
'@
$tmp = Join-Path $env:TEMP "gpf_hook_test.py"
Set-Content -Encoding utf8 $tmp $code
py -3 $tmp $RepoRoot
if ($LASTEXITCODE -ne 0) { Write-Host "Hook-Tests FAIL"; $fail++ } else { Write-Host "Hook-Tests OK" -ForegroundColor Green }

# --- Policy path unit ---
$polCode = @'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]) / "proxy"))
import xai_filter_proxy as p
p.POLICY = p.load_policy(Path(sys.argv[1]) / "proxy" / "policy.json")
assert p.path_allowed("POST", "/v1/chat/completions")[0] is True
assert p.path_allowed("GET", "/v1/storage")[0] is False
assert p.path_allowed("PUT", "/v1/settings")[0] is False
assert p.path_allowed("GET", "/v1/settings")[0] is True
print("OK policy unit")
'@
$tmp2 = Join-Path $env:TEMP "gpf_pol_test.py"
Set-Content -Encoding utf8 $tmp2 $polCode
py -3 $tmp2 $RepoRoot
if ($LASTEXITCODE -ne 0) { Write-Host "Policy unit FAIL"; $fail++ } else { Write-Host "Policy unit OK" -ForegroundColor Green }

# --- Live proxy smoke on 18745 ---
Write-Host "Proxy-Smoke port 18745..."
$py = (py -3 -c "import sys; print(sys.executable)").Trim()
$proxyScript = Join-Path $RepoRoot "proxy\xai_filter_proxy.py"
$policy = Join-Path $RepoRoot "proxy\policy.json"
$proc = Start-Process -PassThru -WindowStyle Hidden -FilePath $py -ArgumentList @(
  $proxyScript, "--port", "18745", "--policy", $policy
)
Start-Sleep -Seconds 1
try {
  try {
    Invoke-WebRequest -Uri "http://127.0.0.1:18745/v1/storage" -UseBasicParsing -TimeoutSec 5 | Out-Null
    Write-Host "FAIL storage should 403"; $fail++
  } catch {
    $code = [int]$_.Exception.Response.StatusCode
    if ($code -ne 403) { Write-Host "FAIL storage $code"; $fail++ } else { Write-Host "OK storage 403" -ForegroundColor Green }
  }
  try {
    $h = Invoke-WebRequest -Uri "http://127.0.0.1:18745/_gpf/health" -UseBasicParsing -TimeoutSec 5
    if ($h.StatusCode -ne 200) { Write-Host "FAIL health"; $fail++ } else { Write-Host "OK health 200" -ForegroundColor Green }
  } catch {
    Write-Host "FAIL health $($_.Exception.Message)"; $fail++
  }
} finally {
  if ($proc -and -not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
}

if ($fail -gt 0) {
  Write-Host "FAILED ($fail)" -ForegroundColor Red
  exit 1
}
Write-Host "Alles gruen." -ForegroundColor Green
exit 0
