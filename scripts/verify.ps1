# Schnelltest: Proxy-Allow/Deny + Hook-Unit
$ErrorActionPreference = "Continue"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Write-Host "Repo: $RepoRoot"

# Hook tests
$env:PYTHONPATH = ""
$code = @"
import json, subprocess, sys
from pathlib import Path
script = Path(r"$RepoRoot") / "hooks" / "block-xai-upload.py"
cases = [
  ("deny curl", {"toolName":"run_terminal_command","toolInput":{"command":"curl -X POST https://cli-chat-proxy.grok.com/v1/storage -d x"}}, "deny"),
  ("allow git", {"toolName":"run_terminal_command","toolInput":{"command":"git status"}}, "allow"),
  ("deny fetch", {"toolName":"web_fetch","toolInput":{"url":"https://x.ai/"}}, "deny"),
  ("allow read", {"toolName":"read_file","toolInput":{"target_file":"a.py"}}, "allow"),
]
fail=0
for name, payload, expect in cases:
  p=subprocess.run([sys.executable, str(script)], input=json.dumps(payload), text=True, capture_output=True)
  d=json.loads(p.stdout.strip()).get("decision")
  ok = d==expect
  print(("OK" if ok else "FAIL"), name, "got", d)
  fail += 0 if ok else 1
sys.exit(fail)
"@
$tmp = Join-Path $env:TEMP "gpf_hook_test.py"
Set-Content -Encoding utf8 $tmp $code
py -3 $tmp
if ($LASTEXITCODE -ne 0) { Write-Host "Hook-Tests FEHLGESCHLAGEN" -ForegroundColor Red; exit 1 }
Write-Host "Hook-Tests OK" -ForegroundColor Green

# Proxy block test (kurz starten)
Write-Host "Proxy-Smoke (Port 18744)..."
$proxyJob = Start-Process -PassThru -WindowStyle Hidden -FilePath "py" -ArgumentList @(
  "-3", (Join-Path $RepoRoot "proxy\xai_filter_proxy.py"), "--port", "18744"
)
Start-Sleep -Seconds 1
try {
  try {
    Invoke-WebRequest -Uri "http://127.0.0.1:18744/v1/storage" -UseBasicParsing -TimeoutSec 5 | Out-Null
    Write-Host "FAIL: storage sollte 403 sein" -ForegroundColor Red
    exit 1
  } catch {
    $code = [int]$_.Exception.Response.StatusCode
    if ($code -ne 403) { Write-Host "FAIL status $code"; exit 1 }
    Write-Host "OK storage -> 403" -ForegroundColor Green
  }
} finally {
  if ($proxyJob -and -not $proxyJob.HasExited) { Stop-Process -Id $proxyJob.Id -Force -ErrorAction SilentlyContinue }
}
Write-Host "Alles gruen." -ForegroundColor Green
