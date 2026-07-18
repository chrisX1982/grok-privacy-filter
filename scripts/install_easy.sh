#!/usr/bin/env bash
# Grok Privacy Filter — Einfacher Quick-Install für die meisten Nutzer (empfohlen)
# Macht die wichtigsten Defaults: Hook + Proxy + GUI + Opt-out + Proxy starten
# Danach wird die Live-GUI gestartet.
#
# Aufruf:
#   bash scripts/install_easy.sh
#
# Für Power-User: install.sh + manuelle Schritte oder install_all (falls vorhanden)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GROK_HOME="${GROK_HOME:-$HOME/.grok}"
PROXY_DIR="$GROK_HOME/proxy"

echo "=== Grok Privacy Filter — EINFACHER INSTALL (GUI-fokussiert) ==="
echo "Dieser Weg ist für die meisten Nutzer gedacht."
echo ""

# 1. Kern-Installation
echo "--- Kern-Installation (Hook + Proxy + GUI) ---"
bash "$REPO_ROOT/scripts/install.sh"

# 2. Privacy Opt-Out
echo ""
echo "--- Privacy Opt-out (Server) ---"
if command -v python3 >/dev/null 2>&1; then
    python3 "$REPO_ROOT/config/privacy-opt-out.py" || {
        echo "WARN: Opt-out konnte nicht automatisch laufen (Login?)."
        echo "   Später manuell: python3 config/privacy-opt-out.py"
    }
elif command -v python >/dev/null 2>&1; then
    python "$REPO_ROOT/config/privacy-opt-out.py" || {
        echo "WARN: Opt-out konnte nicht automatisch laufen."
    }
else
    echo "WARN: Kein Python gefunden für Opt-out."
fi

# 3. Proxy sicherstellen
echo ""
echo "--- Proxy sicherstellen ---"
python3 "$PROXY_DIR/ensure_proxy.py" -v || python "$PROXY_DIR/ensure_proxy.py" -v || true

# 4. GUI starten (wenn möglich im Hintergrund / neues Fenster)
echo ""
echo "--- Starte Live-GUI ---"
GUI_SCRIPT="$PROXY_DIR/live_proxy_gui.py"
LAUNCHER="$PROXY_DIR/start_live_gui.sh"

if [[ -f "$LAUNCHER" ]]; then
    echo "Starte über Launcher..."
    nohup bash "$LAUNCHER" > /dev/null 2>&1 &
elif [[ -f "$GUI_SCRIPT" ]]; then
    echo "Starte GUI direkt..."
    if command -v python3 >/dev/null 2>&1; then
        nohup python3 "$GUI_SCRIPT" > /dev/null 2>&1 &
    else
        nohup python "$GUI_SCRIPT" > /dev/null 2>&1 &
    fi
else
    echo "GUI-Skript nicht gefunden. Starte manuell: python3 ~/.grok/proxy/live_proxy_gui.py"
fi

echo ""
echo "=== Fertig! ==="
echo " - Verwende zukünftig: $LAUNCHER  oder die Desktop-Verknüpfung (Windows)"
echo " - Proxy + voller Datenklau-Schutz sind (oder werden) aktiv."
echo " - In Grok: /new"
echo " - Hooks aktivieren: /hooks-trust (lokalem Hook vertrauen)"
echo " - Dann /hooks öffnen und 'r' zum Reload"
echo " - In der GUI: Menü Aktionen → 'Hooks prüfen' zum Verifizieren"
echo ""
echo "Tipp: Für mehr (VS Code, Autostart) siehe docs/ANLEITUNG.md"
echo "Dokumentation: docs/ANLEITUNG.md  |  Grenzen: docs/GRENZEN.md"
