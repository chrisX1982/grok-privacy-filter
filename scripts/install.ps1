# Grok Privacy Filter — Installation (Windows PowerShell)
# Installiert Hook + Config-Snippet + optional Proxy-Shortcut unter %USERPROFILE%\.grok\
# Aufruf aus Repo-Root:
#   powershell -ExecutionPolicy Bypass -File scripts\install.ps1

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$GrokHome = Join-Path $env:USERPROFILE ".grok"
$HooksDir = Join-Path $GrokHome "hooks"
$ProxyDir = Join-Path $GrokHome "proxy"

Write-Host "=== Grok Privacy Filter Install ===" -ForegroundColor Cyan
Write-Host "Repo: $RepoRoot"
Write-Host "Ziel: $GrokHome"

New-Item -ItemType Directory -Force -Path $HooksDir | Out-Null
New-Item -ItemType Directory -Force -Path $ProxyDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $ProxyDir "logs") | Out-Null

# --- Hook ---
$HookPy = Join-Path $RepoRoot "hooks\block-xai-upload.py"
$HookDestPy = Join-Path $HooksDir "block-xai-upload.py"
Copy-Item -Force $HookPy $HookDestPy

# Python finden
$py = $null
foreach ($c in @("py -3", "python", "python3")) {
  try {
    if ($c -eq "py -3") {
      $v = & py -3 -c "import sys; print(sys.executable)" 2>$null
    } else {
      $v = & $c -c "import sys; print(sys.executable)" 2>$null
    }
    if ($LASTEXITCODE -eq 0 -and $v) { $py = $v.Trim(); break }
  } catch {}
}
if (-not $py) {
  Write-Warning "Python nicht gefunden. Hook-JSON nutzt 'py -3' als Fallback."
  $hookCmd = "py -3 `"$HookDestPy`""
  $sessionCmd = "py -3 -c `"print('[block-xai-upload] aktiv')`""
} else {
  Write-Host "Python: $py"
  $hookCmd = "`"$py`" `"$HookDestPy`""
  $sessionCmd = "`"$py`" -c `"print('[block-xai-upload] aktiv')`""
}

$hookJson = @{
  hooks = @{
    PreToolUse = @(
      @{
        hooks = @(
          @{
            type = "command"
            command = $hookCmd
            timeout = 10
          }
        )
      }
    )
    SessionStart = @(
      @{
        hooks = @(
          @{
            type = "command"
            command = $sessionCmd
            timeout = 5
          }
        )
      }
    )
  }
} | ConvertTo-Json -Depth 8

$hookJsonPath = Join-Path $HooksDir "block-xai-upload.json"
# ConvertTo-Json may produce PSCustomObject quirks — write carefully
@"
{
  "hooks": {
    "PreToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": $($hookCmd | ConvertTo-Json),
            "timeout": 10
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": $($sessionCmd | ConvertTo-Json),
            "timeout": 5
          }
        ]
      }
    ]
  }
}
"@ | Set-Content -Encoding utf8 $hookJsonPath

Write-Host "Hook installiert: $hookJsonPath"

# --- Proxy copy ---
Copy-Item -Force (Join-Path $RepoRoot "proxy\xai_filter_proxy.py") (Join-Path $ProxyDir "xai_filter_proxy.py")
Copy-Item -Force (Join-Path $RepoRoot "scripts\start_proxy.cmd") (Join-Path $ProxyDir "start_proxy.cmd") -ErrorAction SilentlyContinue
Copy-Item -Force (Join-Path $RepoRoot "scripts\start_grok_filtered.cmd") (Join-Path $ProxyDir "start_grok_filtered.cmd") -ErrorAction SilentlyContinue
Write-Host "Proxy kopiert nach: $ProxyDir"

# --- Config snippet merge hint ---
$snippet = Join-Path $RepoRoot "config\config.snippet.toml"
$configPath = Join-Path $GrokHome "config.toml"
Write-Host ""
Write-Host "Config-Snippet: $snippet" -ForegroundColor Yellow
if (Test-Path $configPath) {
  Write-Host "Bestehende config.toml: $configPath"
  Write-Host "Bitte Snippet manuell mergen (Installer ueberschreibt config.toml NICHT)."
} else {
  Copy-Item $snippet $configPath
  Write-Host "Neue config.toml aus Snippet angelegt: $configPath"
}

Write-Host ""
Write-Host "Naechste Schritte:" -ForegroundColor Green
Write-Host "  1. python config\privacy-opt-out.py   (Server Opt-out)"
Write-Host "  2. Proxy:  scripts\start_proxy.cmd"
Write-Host "  3. Grok:   scripts\start_grok_filtered.cmd"
Write-Host "  4. In Grok: /hooks  →  r (reload)  → block-xai-upload sichtbar"
Write-Host "  5. Docs:   docs\ANLEITUNG.md"
Write-Host "Fertig."
