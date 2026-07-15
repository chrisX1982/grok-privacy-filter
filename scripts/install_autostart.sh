#!/usr/bin/env bash
# Autostart unter Linux/macOS (user systemd oder LaunchAgent).
# Aufruf: bash scripts/install_autostart.sh
# Entfernen: bash scripts/install_autostart.sh --remove
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GROK_HOME="${GROK_HOME:-$HOME/.grok}"
PROXY_DIR="$GROK_HOME/proxy"
mkdir -p "$PROXY_DIR/logs"
cp -f "$REPO_ROOT/proxy/xai_filter_proxy.py" "$PROXY_DIR/xai_filter_proxy.py"
cp -f "$REPO_ROOT/scripts/ensure_proxy.py" "$PROXY_DIR/ensure_proxy.py"
chmod +x "$PROXY_DIR/ensure_proxy.py" "$PROXY_DIR/xai_filter_proxy.py" || true

ENSURE="$PROXY_DIR/ensure_proxy.py"
PY="$(command -v python3 || command -v python)"

if [[ "${1:-}" == "--remove" ]]; then
  if [[ "$(uname)" == "Darwin" ]]; then
    launchctl unload "$HOME/Library/LaunchAgents/com.grok.privacy-filter.proxy.plist" 2>/dev/null || true
    rm -f "$HOME/Library/LaunchAgents/com.grok.privacy-filter.proxy.plist"
    echo "LaunchAgent entfernt."
  else
    systemctl --user disable --now grok-privacy-filter-proxy.service 2>/dev/null || true
    rm -f "$HOME/.config/systemd/user/grok-privacy-filter-proxy.service"
    systemctl --user daemon-reload 2>/dev/null || true
    echo "systemd user unit entfernt."
  fi
  exit 0
fi

if [[ "$(uname)" == "Darwin" ]]; then
  PLIST="$HOME/Library/LaunchAgents/com.grok.privacy-filter.proxy.plist"
  mkdir -p "$(dirname "$PLIST")"
  cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.grok.privacy-filter.proxy</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PY</string>
    <string>$ENSURE</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><false/>
</dict>
</plist>
EOF
  launchctl unload "$PLIST" 2>/dev/null || true
  launchctl load "$PLIST"
  echo "LaunchAgent: $PLIST"
else
  UNIT_DIR="$HOME/.config/systemd/user"
  mkdir -p "$UNIT_DIR"
  cat > "$UNIT_DIR/grok-privacy-filter-proxy.service" <<EOF
[Unit]
Description=Grok Privacy Filter Proxy (ensure)
After=network.target

[Service]
Type=oneshot
ExecStart=$PY $ENSURE
RemainAfterExit=yes

[Install]
WantedBy=default.target
EOF
  systemctl --user daemon-reload
  systemctl --user enable --now grok-privacy-filter-proxy.service
  echo "systemd user: grok-privacy-filter-proxy.service"
fi

"$PY" "$ENSURE"
echo "Fertig."
