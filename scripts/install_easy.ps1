# Grok Privacy Filter — Einfacher Quick-Install für die meisten Nutzer (empfohlen)
# Macht die wichtigsten Defaults: Hook + Proxy + GUI + Opt-out + Proxy starten
# Danach wird direkt die Live-GUI geöffnet.
#
# Aufruf:
#   powershell -ExecutionPolicy Bypass -File .\scripts\install_easy.ps1
#
# Für Power-User / VS Code: install_all.ps1 verwenden

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RepoRoot

Write-Host "=== Grok Privacy Filter — EINFACHER INSTALL (GUI-fokussiert) ===" -ForegroundColor Cyan
Write-Host "Dieser Weg ist für die meisten Nutzer gedacht." -ForegroundColor Green
Write-Host ""

# 1. Kern-Installation (Hook, Proxy-Dateien, GUI, Desktop-Link, Config-Snippet)
Write-Host "--- Kern-Installation (Hook + Proxy + GUI) ---" -ForegroundColor Yellow
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $RepoRoot "scripts\install.ps1")

# 2. Privacy Opt-Out (wichtigster Server-Default)
Write-Host ""
Write-Host "--- Privacy Opt-out (Server) ---" -ForegroundColor Yellow
$optOut = Join-Path $RepoRoot "config\privacy-opt-out.py"
if (Test-Path $optOut) {
    try {
        & py -3 $optOut
    } catch {
        Write-Warning "Opt-out konnte nicht automatisch ausgeführt werden (Python oder Login?)."
        Write-Host "   Bitte später manuell: py -3 config\privacy-opt-out.py" -ForegroundColor Yellow
    }
} else {
    Write-Warning "privacy-opt-out.py nicht gefunden."
}

# 3. Proxy sicherstellen
Write-Host ""
Write-Host "--- Proxy sicherstellen ---" -ForegroundColor Yellow
$ProxyDir = Join-Path $env:USERPROFILE ".grok\proxy"
& py -3 (Join-Path $ProxyDir "ensure_proxy.py") -v

# 4. GUI starten (empfohlener Einstieg)
Write-Host ""
Write-Host "--- Starte Live-GUI ---" -ForegroundColor Green
$guiBat = Join-Path $ProxyDir "start_live_gui.bat"
if (Test-Path $guiBat) {
    Write-Host "GUI wird in neuem Fenster gestartet..."
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c `"$guiBat`"" -WindowStyle Normal
} else {
    Write-Host "GUI direkt starten..."
    & py -3 (Join-Path $ProxyDir "live_proxy_gui.py")
}

Write-Host ""
Write-Host "=== Fertig! ===" -ForegroundColor Green
Write-Host " - Desktop-Verknüpfung 'Proxy Live Status' wurde angelegt (für zukünftige Starts)"
Write-Host " - Die GUI sollte jetzt offen sein. Proxy + voller Datenklau-Schutz sind aktiv."
Write-Host " - In Grok: /new  (oder VS Code Window neu laden)"
Write-Host ""
Write-Host "Tipp: Für VS Code + Autostart später: scripts\install_all.ps1 verwenden" -ForegroundColor Cyan
Write-Host "Dokumentation: docs/ANLEITUNG.md  |  Grenzen: docs/GRENZEN.md"
