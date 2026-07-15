# Changelog

## 1.1.0 — 2026-07-15

- `scripts/ensure_proxy.py` — Proxy nur starten, wenn Port frei
- `scripts/install_autostart.ps1` / `.sh` — Login-Autostart
- `scripts/install_vscode.ps1` — Config endpoints + VS Code folderOpen-Task
- `docs/VSCODE.md` — Alltag in der Extension (kein CMD)
- Config-Snippet: `[endpoints] cli_chat_proxy_base_url`
- README/ANLEITUNG an VS-Code-Workflow angepasst

## 1.0.0 — 2026-07-15

Erste öffentliche Paketierung:

- Default-Deny-Proxy `proxy/xai_filter_proxy.py`
- PreToolUse-Hook `hooks/block-xai-upload.py`
- Config-Snippet + Privacy Opt-out Script
- Install/Start/Verify Scripts (Windows + Unix)
- Docs: ANLEITUNG, GRENZEN, WINDOWS-FIREWALL
