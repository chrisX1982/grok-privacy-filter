# Changelog

## 1.2.0 — 2026-07-15

Stabilität und Wartbarkeit (ohne Chat zu killen):

- `proxy/policy.json` — Allow/Deny konfigurierbar
- Proxy: Log-Rotation, `GET /_gpf/health`, klarere BLOCK-Logs
- `ensure_proxy.py` — Health-Check, Watchdog-Modus, kein Kill laufender Proxies
- Autostart mit **absolutem Python-Pfad**
- `install_all.ps1`, `uninstall.ps1`
- SessionStart-Hook `proxy_health_session.py` (warnen + einmal restart-try)
- CI workflow `.github/workflows/verify.yml`
- Docs VSCODE/README angepasst

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
