# One-shot setup: install + opt-out + vscode + autostart + ensure
#   powershell -ExecutionPolicy Bypass -File scripts\install_all.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\install_all.ps1 -Workspace "C:\proj" -SkipOptOut

param(
    [string]$Workspace = "",
    [switch]$SkipOptOut,
    [switch]$SkipVscode,
    [switch]$SkipAutostart,
    [switch]$WatchdogTask
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RepoRoot

Write-Host "=== Grok Privacy Filter install_all ===" -ForegroundColor Cyan

& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $RepoRoot "scripts\install.ps1")
if ($LASTEXITCODE -ne 0 -and $null -ne $LASTEXITCODE) {
  # install.ps1 may not set exit code; continue
}

$ProxyDir = Join-Path $env:USERPROFILE ".grok\proxy"
New-Item -ItemType Directory -Force -Path $ProxyDir | Out-Null
Copy-Item -Force (Join-Path $RepoRoot "proxy\policy.json") (Join-Path $ProxyDir "policy.json")
Copy-Item -Force (Join-Path $RepoRoot "proxy\xai_filter_proxy.py") (Join-Path $ProxyDir "xai_filter_proxy.py")
Copy-Item -Force (Join-Path $RepoRoot "scripts\ensure_proxy.py") (Join-Path $ProxyDir "ensure_proxy.py")

if (-not $SkipOptOut) {
    Write-Host "--- privacy opt-out ---" -ForegroundColor Yellow
    & py -3 (Join-Path $RepoRoot "config\privacy-opt-out.py")
}

if (-not $SkipVscode) {
    Write-Host "--- vscode ---" -ForegroundColor Yellow
    $ws = if ($Workspace) { $Workspace } else { (Get-Location).Path }
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $RepoRoot "scripts\install_vscode.ps1") -Workspace $ws -UserSettings
}

if (-not $SkipAutostart) {
    Write-Host "--- autostart ---" -ForegroundColor Yellow
    if ($WatchdogTask) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $RepoRoot "scripts\install_autostart.ps1") -ScheduledTask -Watchdog
    } else {
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $RepoRoot "scripts\install_autostart.ps1")
    }
}

Write-Host "--- ensure proxy ---" -ForegroundColor Yellow
& py -3 (Join-Path $ProxyDir "ensure_proxy.py") -v

Write-Host ""
Write-Host "Done. In Grok Extension run /new or reload the VS Code window." -ForegroundColor Green
Write-Host "Docs: docs/VSCODE.md"
