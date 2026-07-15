#!/usr/bin/env bash
# Grok Privacy Filter — Installation (macOS/Linux)
# Aufruf aus Repo-Root:  bash scripts/install.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GROK_HOME="${GROK_HOME:-$HOME/.grok}"
HOOKS_DIR="$GROK_HOME/hooks"
PROXY_DIR="$GROK_HOME/proxy"

echo "=== Grok Privacy Filter Install ==="
echo "Repo: $REPO_ROOT"
echo "Ziel: $GROK_HOME"

mkdir -p "$HOOKS_DIR" "$PROXY_DIR/logs"

cp -f "$REPO_ROOT/hooks/block-xai-upload.py" "$HOOKS_DIR/block-xai-upload.py"
chmod +x "$HOOKS_DIR/block-xai-upload.py" "$REPO_ROOT/proxy/xai_filter_proxy.py" || true

PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1; then
    PY="$(command -v "$c")"
    break
  fi
done
if [[ -z "$PY" ]]; then
  echo "WARN: Python nicht gefunden — Hook nutzt 'python3' als Befehl."
  PY="python3"
fi
echo "Python: $PY"

HOOK_CMD="$PY $HOOKS_DIR/block-xai-upload.py"
SESSION_CMD="$PY -c \"print('[block-xai-upload] aktiv')\""

cat > "$HOOKS_DIR/block-xai-upload.json" <<EOF
{
  "hooks": {
    "PreToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$HOOK_CMD",
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
            "command": $SESSION_CMD,
            "timeout": 5
          }
        ]
      }
    ]
  }
}
EOF

# Fix SessionStart JSON (command must be a string)
cat > "$HOOKS_DIR/block-xai-upload.json" <<EOF
{
  "hooks": {
    "PreToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$HOOK_CMD",
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
            "command": "$PY -c \"print('[block-xai-upload] aktiv')\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
EOF

echo "Hook: $HOOKS_DIR/block-xai-upload.json"

cp -f "$REPO_ROOT/proxy/xai_filter_proxy.py" "$PROXY_DIR/xai_filter_proxy.py"
cp -f "$REPO_ROOT/scripts/ensure_proxy.py" "$PROXY_DIR/ensure_proxy.py"
cp -f "$REPO_ROOT/scripts/start_proxy.sh" "$PROXY_DIR/start_proxy.sh" 2>/dev/null || true
cp -f "$REPO_ROOT/scripts/start_grok_filtered.sh" "$PROXY_DIR/start_grok_filtered.sh" 2>/dev/null || true
chmod +x "$PROXY_DIR/"*.sh "$PROXY_DIR/"*.py 2>/dev/null || true

CONFIG="$GROK_HOME/config.toml"
if [[ -f "$CONFIG" ]] && ! grep -q 'cli_chat_proxy_base_url' "$CONFIG"; then
  cat >> "$CONFIG" <<'EOF'

# Grok Privacy Filter — Chat ueber lokalen Proxy
[endpoints]
cli_chat_proxy_base_url = "http://127.0.0.1:18743/v1"
EOF
  echo "endpoints an config.toml angehaengt."
fi

SNIPPET="$REPO_ROOT/config/config.snippet.toml"
CONFIG="$GROK_HOME/config.toml"
if [[ -f "$CONFIG" ]]; then
  echo "Bestehende config.toml — Snippet manuell mergen: $SNIPPET"
else
  cp "$SNIPPET" "$CONFIG"
  echo "config.toml angelegt: $CONFIG"
fi

echo ""
echo "Naechste Schritte:"
echo "  1. python3 config/privacy-opt-out.py"
echo "  2. bash scripts/install_autostart.sh"
echo "  3. python3 $PROXY_DIR/ensure_proxy.py"
echo "  4. VS Code: siehe docs/VSCODE.md (tasks.json aus vscode/ kopieren)"
echo "  5. docs/ANLEITUNG.md + docs/VSCODE.md"
echo "Fertig."
