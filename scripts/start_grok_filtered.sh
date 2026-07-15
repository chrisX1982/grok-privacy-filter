#!/usr/bin/env bash
set -euo pipefail
# Grok ueber lokalen Filter-Proxy (Proxy muss laufen: start_proxy.sh)

export GROK_CLI_CHAT_PROXY_BASE_URL="${GROK_CLI_CHAT_PROXY_BASE_URL:-http://127.0.0.1:18743/v1}"
export GROK_TELEMETRY_ENABLED=0
export GROK_FEEDBACK_ENABLED=0
export GROK_MEMORY=0

echo "[filter] GROK_CLI_CHAT_PROXY_BASE_URL=$GROK_CLI_CHAT_PROXY_BASE_URL"
echo "[filter] Telemetry/Feedback/Memory env = off"
echo "[filter] Proxy muss laufen: scripts/start_proxy.sh"

if command -v grok >/dev/null 2>&1; then
  exec grok "$@"
elif [[ -x "$HOME/.grok/bin/grok" ]]; then
  exec "$HOME/.grok/bin/grok" "$@"
else
  echo "grok nicht gefunden (PATH oder ~/.grok/bin/grok)" >&2
  exit 1
fi
