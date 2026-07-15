# Entfernt Grok Privacy Filter Bestandteile (sicher, kein System-Kill)
#   powershell -ExecutionPolicy Bypass -File scripts\uninstall.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\uninstall.ps1 -RemoveConfigEndpoints
#   powershell -ExecutionPolicy Bypass -File scripts\uninstall.ps1 -KillProxy

param(
    [switch]$RemoveConfigEndpoints,
    [switch]$KillProxy,
    [string]$Workspace = ""
)

$ErrorActionPreference = "Continue"
$GrokHome = Join-Path $env:USERPROFILE ".grok"
$ProxyDir = Join-Path $GrokHome "proxy"
$HooksDir = Join-Path $GrokHome "hooks"
$Startup = [Environment]::GetFolderPath("Startup")
$TaskName = "GrokPrivacyFilterProxy"

Write-Host "=== Grok Privacy Filter — uninstall ===" -ForegroundColor Cyan

# Autostart
$vbs = Join-Path $Startup "GrokPrivacyFilterProxy.vbs"
if (Test-Path $vbs) {
    Remove-Item -Force $vbs
    Write-Host "Removed Startup VBS"
}
$t = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($t) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Removed scheduled task $TaskName"
}
$t2 = Get-ScheduledTask -TaskName "GrokPrivacyFilterWatchdog" -ErrorAction SilentlyContinue
if ($t2) {
    Unregister-ScheduledTask -TaskName "GrokPrivacyFilterWatchdog" -Confirm:$false
    Write-Host "Removed watchdog task"
}

# Hooks
foreach ($f in @("block-xai-upload.py", "block-xai-upload.json", "proxy-health-session.py")) {
    $p = Join-Path $HooksDir $f
    if (Test-Path $p) {
        Remove-Item -Force $p
        Write-Host "Removed hook $f"
    }
}

# Proxy files (optional keep logs)
if (Test-Path $ProxyDir) {
    Get-ChildItem $ProxyDir -File | Where-Object { $_.Name -ne "logs" } | ForEach-Object {
        if ($_.DirectoryName -like "*\logs") { return }
        Remove-Item -Force $_.FullName -ErrorAction SilentlyContinue
    }
    # remove py/json at proxy root
    foreach ($name in @("xai_filter_proxy.py", "ensure_proxy.py", "policy.json", "start_proxy.cmd", "start_grok_filtered.cmd", "start_proxy_silent.vbs", "start_proxy_silent.cmd")) {
        $p = Join-Path $ProxyDir $name
        if (Test-Path $p) { Remove-Item -Force $p; Write-Host "Removed $name" }
    }
}

# Workspace task
if (-not $Workspace) { $Workspace = (Get-Location).Path }
$tasks = Join-Path $Workspace ".vscode\tasks.json"
if (Test-Path $tasks) {
    try {
        $j = Get-Content $tasks -Raw | ConvertFrom-Json
        $rest = @($j.tasks | Where-Object { $_.label -ne "Grok Privacy: Ensure Filter Proxy" })
        if ($rest.Count -eq 0) {
            # restore backup if exists
            if (Test-Path ($tasks + ".gpf-backup")) {
                Copy-Item -Force ($tasks + ".gpf-backup") $tasks
                Write-Host "Restored tasks.json from gpf-backup"
            } else {
                Remove-Item -Force $tasks
                Write-Host "Removed tasks.json (only GPF task)"
            }
        } else {
            Write-Host "Bitte GPF-Task manuell aus tasks.json entfernen (andere Tasks vorhanden)."
        }
    } catch {
        Write-Warning "tasks.json nicht geparst: $_"
    }
}

# Config endpoints strip (optional)
$cfg = Join-Path $GrokHome "config.toml"
if ($RemoveConfigEndpoints -and (Test-Path $cfg)) {
    $lines = Get-Content $cfg
    $out = New-Object System.Collections.Generic.List[string]
    $skip = $false
    foreach ($line in $lines) {
        if ($line -match '^\s*\[endpoints\]\s*$') { $skip = $true; continue }
        if ($skip -and $line -match '^\s*\[') { $skip = $false }
        if ($skip -and $line -match 'cli_chat_proxy_base_url') { continue }
        if ($skip -and ($line.Trim() -eq "" -or $line -match '^\s*#')) { continue }
        if ($skip) { continue }
        if ($line -match 'cli_chat_proxy_base_url') { continue }
        $out.Add($line)
    }
    Copy-Item -Force $cfg ($cfg + ".pre-uninstall-backup")
    Set-Content -Path $cfg -Value ($out -join "`r`n") -Encoding utf8
    Write-Host "Stripped endpoints from config.toml (backup .pre-uninstall-backup)"
    Write-Host "WICHTIG: Ohne lokalen Proxy zeigt Grok wieder direkt auf xAI (oder bricht bis Config ok)."
}

if ($KillProxy) {
    # Best effort: processes listening on 18743
    try {
        $conns = Get-NetTCPConnection -LocalPort 18743 -ErrorAction SilentlyContinue
        foreach ($c in $conns) {
            if ($c.OwningProcess) {
                Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
                Write-Host "Stopped PID $($c.OwningProcess) on 18743"
            }
        }
    } catch {
        Write-Warning "KillProxy: $_"
    }
}

Write-Host "Uninstall done. Grok kann ohne Filter weiterlaufen (je nach config)."
