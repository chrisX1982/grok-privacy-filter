# Grok Privacy Filter — VS Code / Cursor Extension

For everyone who does **not** use the terminal TUI but works with **Grok Build inside VS Code** (or Cursor) in the chat panel.

---

## Important: No extra CMD window required

| Myth | Reality |
|------|---------|
| "Start a new CMD" | Only needed for the **terminal TUI** (`grok` in the integrated terminal). |
| **VS Code Extension** | Reads **`~/.grok/config.toml`**. The proxy must run in the **background**. |

The filter is active in the extension when:

1. **`[endpoints] cli_chat_proxy_base_url`** points to the local proxy, and
2. the **proxy is running on port 18743**, and
3. you start a **new session** (`/new` or reload window) — old sessions often keep the old upstream URL.

---

## One-time setup (Windows)

**One command (recommended):**

```powershell
cd C:\Path\to\grok-privacy-filter
powershell -ExecutionPolicy Bypass -File .\scripts\install_all.ps1 -Workspace "C:\Path\to\your\project"
```

Optional with watchdog (restarts proxy every 90s if it crashes):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_all.ps1 -Workspace "C:\your\project" -WatchdogTask
```

**Or step by step:**

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
py -3 .\config\privacy-opt-out.py
powershell -ExecutionPolicy Bypass -File .\scripts\install_vscode.ps1 -Workspace "C:\Path\to\your\project" -UserSettings
powershell -ExecutionPolicy Bypass -File .\scripts\install_autostart.ps1
# optional: -Watchdog
```

### What `install_vscode.ps1` does

| Action | Detail |
|--------|--------|
| Proxy files | copied to `~/.grok/proxy/` (incl. `ensure_proxy.py`) |
| Config | sets/appends `cli_chat_proxy_base_url = "http://127.0.0.1:18743/v1"` |
| `.vscode/tasks.json` | Task **"Grok Privacy: Ensure Filter Proxy"** with `runOn: folderOpen` |
| `-UserSettings` | sets `task.allowAutomaticTasks: "on"` in Code/Cursor user settings (backup `.gpf-backup`) |
| Immediately | calls `ensure_proxy.py` |

### What `install_autostart.ps1` does

| Action | Detail |
|--------|--------|
| Startup folder | `GrokPrivacyFilterProxy.vbs` with **absolute Python path** (no PATH guessing) |
| `-ScheduledTask` | scheduled task at logon + restart |
| `-Watchdog` | additional loop `ensure_proxy --watchdog` every 90s |
| `-Remove` | removes autostart + tasks |

### Uninstallation

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\uninstall.ps1
# optional endpoints from config + proxy process:
powershell -ExecutionPolicy Bypass -File .\scripts\uninstall.ps1 -RemoveConfigEndpoints -KillProxy
```

---

## Daily usage (after setup)

1. **PC on** → autostart launches the proxy (if installed).
2. **Open VS Code** → on folder open the task runs again (if allowed) and starts the proxy only if it is **not** already running.
3. **Grok Extension** → chat normally.
4. After config changes: **`/new`** or **Reload Window**.

Force proxy manually:

```powershell
py -3 $env:USERPROFILE\.grok\proxy\ensure_proxy.py
```

---

## Config (core for the extension)

In `~/.grok/config.toml`:

```toml
[endpoints]
cli_chat_proxy_base_url = "http://127.0.0.1:18743/v1"
```

This is the switch used by **both CLI and Extension** for the chat proxy.
Without a running proxy: connections fail (port closed) — then use `ensure_proxy.py`.

Additional hardening: `config/config.snippet.toml` (telemetry off, …).

---

## Hook in the extension

Hooks live globally under `~/.grok/hooks/` and also apply inside the extension.

- Install: `install.ps1`
- Verify: in Grok **`/hooks-trust`** → then `/hooks` → reload **`r`** → `block-xai-upload` visible
- The hook blocks **agent tools** (curl to xAI etc.), **not** the internal chat path (that's what the proxy is for).

---

## Automatic tasks in VS Code

On first `folderOpen`, VS Code may ask whether to allow tasks.

- Allow it, **or**
- User setting: `"task.allowAutomaticTasks": "on"` (set via `-UserSettings`)

Run task manually: **Terminal → Run Task… → "Grok Privacy: Ensure Filter Proxy"**.

Template in the repo: `vscode/tasks.json` (copy it to `.vscode/tasks.json`).

---

## Cursor

Same mechanisms (`~/.grok/`, tasks, `ensure_proxy`).
`-UserSettings` also writes to `%APPDATA%\Cursor\User\settings.json` when present.

---

## Troubleshooting (Extension)

| Symptom | Cause / Fix |
|---------|-------------|
| Chat does not work at all | Proxy off → `ensure_proxy.py`; port 18743 occupied by another process? |
| Chat works but "unfiltered"? | Old session → `/new`; check `cli_chat_proxy_base_url` in config |
| Task never starts | `task.allowAutomaticTasks`; trust the workspace |
| Hook missing | `install.ps1`, then `/hooks-trust`; `/hooks` → `r` |
| Dead after reboot | re-run `install_autostart.ps1` |
| tasks.json overwritten | Backup: `.vscode/tasks.json.gpf-backup` |

Proxy logs:

- `~/.grok/proxy/logs/ensure-proxy-daemon.log`
- `~/.grok/proxy/logs/proxy-YYYY-MM-DD.log` (when the proxy itself logs)
- Repo: `logs/proxy-*.log` when started from the repo

---

## Terminal TUI vs Extension

| Start method | What you need |
|--------------|---------------|
| **VS Code Extension** (this doc) | `config.toml` endpoints + `ensure_proxy` / autostart / folderOpen task |
| **Terminal `grok`** | optional `start_grok_filtered.cmd` **or** the same `config.toml` endpoints |

With `cli_chat_proxy_base_url` set in the config you do **not** need `GROK_CLI_CHAT_PROXY_BASE_URL` in the environment — it applies to both CLI and extension.

---

## Related docs

- [INSTRUCTIONS.md](INSTRUCTIONS.md) — overall flow
- [LIMITS.md](LIMITS.md) — what the proxy cannot do
- [WINDOWS-FIREWALL.md](WINDOWS-FIREWALL.md) — optional host blocks
