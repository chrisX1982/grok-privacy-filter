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
$HealthPySrc = Join-Path $RepoRoot "hooks\proxy_health_session.py"
$HealthDest = Join-Path $HooksDir "proxy_health_session.py"
if (Test-Path $HealthPySrc) { Copy-Item -Force $HealthPySrc $HealthDest }

if (-not $py) {
  Write-Warning "Python nicht gefunden. Hook-JSON nutzt 'py -3' als Fallback."
  $hookCmd = "py -3 `"$HookDestPy`""
  $healthCmd = "py -3 `"$HealthDest`""
} else {
  Write-Host "Python: $py"
  $hookCmd = "`"$py`" `"$HookDestPy`""
  $healthCmd = "`"$py`" `"$HealthDest`""
}

$hookJsonPath = Join-Path $HooksDir "block-xai-upload.json"
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
            "command": $($healthCmd | ConvertTo-Json),
            "timeout": 15
          }
        ]
      }
    ]
  }
}
"@ | Set-Content -Encoding utf8 $hookJsonPath

Write-Host "Hook installiert: $hookJsonPath (PreToolUse upload-block + SessionStart proxy-health)"

# --- Proxy + ensure_proxy + policy + Live-GUI ---
Copy-Item -Force (Join-Path $RepoRoot "proxy\xai_filter_proxy.py") (Join-Path $ProxyDir "xai_filter_proxy.py")
Copy-Item -Force (Join-Path $RepoRoot "proxy\policy.json") (Join-Path $ProxyDir "policy.json")
Copy-Item -Force (Join-Path $RepoRoot "scripts\ensure_proxy.py") (Join-Path $ProxyDir "ensure_proxy.py")
Copy-Item -Force (Join-Path $RepoRoot "proxy\live_proxy_gui.py") (Join-Path $ProxyDir "live_proxy_gui.py") -ErrorAction SilentlyContinue
Copy-Item -Force (Join-Path $RepoRoot "scripts\start_proxy.cmd") (Join-Path $ProxyDir "start_proxy.cmd") -ErrorAction SilentlyContinue
Copy-Item -Force (Join-Path $RepoRoot "scripts\start_grok_filtered.cmd") (Join-Path $ProxyDir "start_grok_filtered.cmd") -ErrorAction SilentlyContinue

# Desktop-Verknüpfung für Live-GUI anlegen
$desktop = [Environment]::GetFolderPath("Desktop")
$guiBat = Join-Path $ProxyDir "start_live_gui.bat"
@"
@echo off
cd /d "%~dp0"
python live_proxy_gui.py
"@ | Set-Content -Path $guiBat -Encoding ASCII

$shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut("$desktop\Proxy Live Status.lnk")
$shortcut.TargetPath = $guiBat
$shortcut.WorkingDirectory = $ProxyDir
$shortcut.Description = "Grok Proxy Live-Anzeige + Datenklau-Schutz"
$shortcut.Save()

Write-Host "Proxy + Live-GUI kopiert nach: $ProxyDir"
Write-Host "  - live_proxy_gui.py = zentrale Oberfläche (Start + Datenklau-Schutz + Einstellungen)"
Write-Host "  - Desktop-Verknüpfung 'Proxy Live Status' angelegt"

# endpoints in config (VS Code Extension)
$ConfigPath = Join-Path $GrokHome "config.toml"
$endpointNeedle = "cli_chat_proxy_base_url"
$endpointBlock = @"

# Grok Privacy Filter — Chat ueber lokalen Proxy (Extension + CLI)
[endpoints]
cli_chat_proxy_base_url = "http://127.0.0.1:18743/v1"
"@
if (Test-Path $ConfigPath) {
  $rawCfg = Get-Content $ConfigPath -Raw
  if ($rawCfg -notmatch [regex]::Escape($endpointNeedle)) {
    Add-Content -Path $ConfigPath -Value $endpointBlock
    Write-Host "endpoints an config.toml angehaengt."
  }
}

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
Write-Host "  1. py -3 config\privacy-opt-out.py"
Write-Host "  2. VS Code Extension (empfohlen):"
Write-Host "       powershell -ExecutionPolicy Bypass -File scripts\install_vscode.ps1 -Workspace . -UserSettings"
Write-Host "  3. Autostart Proxy:"
Write-Host "       powershell -ExecutionPolicy Bypass -File scripts\install_autostart.ps1"
Write-Host "  4. Proxy jetzt:  py -3 $ProxyDir\ensure_proxy.py"
Write-Host "  5. Docs: docs\VSCODE.md  und  docs\ANLEITUNG.md"
Write-Host "Fertig."
