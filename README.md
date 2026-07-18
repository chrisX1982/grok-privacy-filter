# Grok Privacy Filter

**Community hardening** for the [Grok Build CLI](https://x.ai) (xAI):  
reduced unnecessary uploads, Coding-Data-Retention **opt-out**, agent hook, and a local **default-deny proxy**.

> **Two paths:**
> - **Easy (recommended for most users):** `install_easy.*` + **Live GUI** (5 minutes, one toggle)
> - **Advanced / VS Code:** `install_all.ps1` + full control

> **Deutsch:** Community-Schutzmaßnahmen für die Grok Build CLI. Siehe [README.de.md](README.de.md) für die deutsche Version.

---

## Why this exists

In July 2026 it became public that Grok Build could send **repository contents** (Git bundles) to cloud storage — regardless of which files the agent had actually "read". xAI pointed to **`/privacy`**, ZDR (Enterprise), and later server-side flags.

This repository bundles **immediately usable** countermeasures for individuals:

| Layer | Tool | Effect |
|-------|------|--------|
| 1 | `config/privacy-opt-out.py` | API: `codingDataRetentionOptOut=true` |
| 2 | `config/config.snippet.toml` | Disables telemetry/trace/prefetch/indexing + sets **endpoints proxy** |
| 3 | `hooks/block-xai-upload.*` | Prevents agent tools from pushing to xAI/GCS |
| 4 | `proxy/xai_filter_proxy.py` + `ensure_proxy.py` | Default-deny proxy; only starts when needed |
| 5 | Autostart / VS Code Task | Starts proxy at login or when opening the workspace |
| 6 | (optional) Firewall | Allow only auth + local proxy — see docs |

**Live GUI (recommended for normal users):** `proxy/live_proxy_gui.py` (copied to `~/.grok/proxy/` during install)

- Menu bar (File / View / Actions / Help / Language)
- Top status (PROXY / PROTECTION), clock, "Always on top" checkbox
- Color banner showing the block list when protection is active
- Log area with color highlighting (ALLOW/BLOCK)
- Bottom buttons: Start Proxy, Stop Proxy, Recommended Defaults, Full Start, Advanced (toggles mode + window size)
- Bottom status bar for feedback
- Fully bilingual (German / English), switchable in the menu
- Settings only via menu (File → Settings...)
- Dynamic paths, instant visual feedback, buttons disable when not applicable

**Live GUI preview:**

![Live GUI preview](Preview_Grok_Privacy_Proxy.PNG)

Launch: double-click the desktop shortcut or run `python proxy/live_proxy_gui.py` (or `~/.grok/proxy/start_live_gui.*`)

This is the simple path: one switch for complete exfiltration protection. No 20 presets.

**Honest scope:** Filters paths on `cli-chat-proxy` (storage/upload default-deny).  
Chat/inference stays usable. It does **not** magically block every host on the internet and does **not** prove server-side deletion.  
See [docs/LIMITS.md](docs/LIMITS.md).

**No marketing speak:** A firewall that blocks all of `grok.exe` kills the CLI.  
**Proxy** keeps the CLI/extension usable while blocking upload paths on the chat host.

---

## Quick start (5 minutes)

### Prerequisites

- Grok Build installed and logged in once with `grok login`
- Python **3.10+** (`python`, `python3`, or Windows `py -3`)

### 1. Easy path (recommended for **most users**)

```powershell
git clone https://github.com/chrisX1982/grok-privacy-filter.git
cd grok-privacy-filter
powershell -ExecutionPolicy Bypass -File .\scripts\install_easy.ps1
```

**The Live GUI opens automatically.**  
Click "Recommended Defaults" or "Full Start" (recommended).  
Afterwards always launch via the desktop shortcut "Proxy Live Status".  
Language is switchable via the "Language" menu.

In Grok: type `/hooks-trust` (trust the local hook).  
Then open `/hooks` and press `r` to reload.  
In the GUI: Actions → "Check Hooks" to verify installation.

> **The GUI is the standard entry point.** Everything else is optional for power users.

### Windows — for VS Code / advanced setup

```powershell
git clone https://github.com/chrisX1982/grok-privacy-filter.git
cd grok-privacy-filter
powershell -ExecutionPolicy Bypass -File .\scripts\install_all.ps1 -Workspace "C:\Path\to\your\project"
```

Then in Grok: `/hooks-trust`, then `/hooks` → `r` to reload.  
GUI: Actions → "Check Hooks".

| Script | Purpose |
|--------|---------|
| **`install_easy.ps1`** / `.sh` | **Recommended for most** (hook + proxy + GUI + opt-out + starts GUI) |
| `install_all.ps1` | Everything in one go (incl. VS Code + autostart) |
| `install.ps1` | Hook, proxy, policy, config endpoints |
| `install_vscode.ps1` | folderOpen task + user settings |
| `install_autostart.ps1` | Login + optional watchdog |
| `ensure_proxy.py` | Starts proxy only if needed; `--watchdog` |
| `uninstall.ps1` | Clean removal |

### Windows — terminal only (optional)

```bat
scripts\start_proxy.cmd
scripts\start_grok_filtered.cmd
```

When using `cli_chat_proxy_base_url` in the config, you often only need `ensure_proxy` + normal `grok`.

### macOS / Linux (easy)

```bash
git clone https://github.com/chrisX1982/grok-privacy-filter.git
cd grok-privacy-filter
bash scripts/install_easy.sh
```

Or manually: `bash scripts/install.sh` + opt-out + ensure.

VS Code: see `docs/VSCODE.md` — copy `vscode/tasks.json` into `.vscode/`.

### Verification

```powershell
# Windows
powershell -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

```bash
curl -i http://127.0.0.1:18743/v1/storage   # expected: 403
curl -i http://127.0.0.1:18743/v1/models    # upstream (e.g. 401 without token = OK)
```

In Grok: `/hooks` → reload → **block-xai-upload** should be active.

---

## Directory structure

```text
grok-privacy-filter/
├── README.md
├── README.de.md
├── LICENSE
├── config/
│   ├── config.snippet.toml      ← includes [endpoints] proxy URL
│   └── privacy-opt-out.py
├── docs/
│   ├── ANLEITUNG.md             ← German
│   ├── INSTRUCTIONS.md          ← English
│   ├── GRENZEN.md               ← German
│   ├── LIMITS.md                ← English
│   ├── VSCODE.md
│   ├── WINDOWS-FIREWALL.md
│   └── GITHUB.md
├── hooks/
│   └── block-xai-upload.*
├── proxy/
│   └── xai_filter_proxy.py
├── vscode/
│   └── tasks.json               ← template for folderOpen → ensure_proxy
└── scripts/
    ├── install.ps1 / install.sh
    ├── install_vscode.ps1
    ├── install_autostart.ps1/.sh
    ├── ensure_proxy.py
    ├── start_proxy.* / start_grok_filtered.*
    └── verify.ps1
```

---

## Proxy: Allow / Deny (core logic)

**Allow (prefixes):**

- `/v1/chat/completions`, `/v1/responses`
- `/v1/models`, `/v1/user`
- `/v1/privacy/coding-data-retention`
- `/v1/settings` — **GET only**

**Deny (data exfiltration):**

- `/v1/storage`, `/v1/upload`, `/storage`
- `/v1/codebase`, `/v1/workspace`, `/v1/sync`
- `/v1/telemetry`, `/v1/feedback`, `/v1/bundle`, `/v1/trace`
- **Default-deny** for everything else

**Live control:** `live_proxy_gui.py` shows status + logs and lets you start/stop + choose presets via menu ("Settings", "Recommended Defaults", "Full Start"). Fully bilingual (DE/EN). No need to manually edit `policy.json`.

Upstream: `https://cli-chat-proxy.grok.com`  
Local: `http://127.0.0.1:18743`  
Env var: `GROK_CLI_CHAT_PROXY_BASE_URL=http://127.0.0.1:18743/v1`

---

## Important CLI facts

| Command | Meaning |
|---------|---------|
| `/privacy opt-out` | Privacy mode (retention + sharing off) |
| `/privacy opt-in` | Share data |
| `/privacy` alone | often shows **empty UI** — argument is required |

API (using session token from `~/.grok/auth.json`):

```http
PUT https://cli-chat-proxy.grok.com/v1/privacy/coding-data-retention
{"codingDataRetentionOptOut": true}
```

Official deletion at xAI: [privacy portal](https://x.ai/privacy-portal) — **not** part of this tool.

---

## Security notes

- **Never** commit `auth.json`, API keys, or session tokens.
- Opt-out and the proxy are **not** legal advice and **do not** prove server-side deletion.
- After Grok updates, re-run verification and review the allow list.
- Rotate any secrets that ever lived in a repo.

---

## Documentation

| File | Content |
|------|---------|
| [docs/VSCODE.md](docs/VSCODE.md) | **VS Code / Cursor Extension** usage — autostart, tasks, config |
| [docs/INSTRUCTIONS.md](docs/INSTRUCTIONS.md) | Complete installation & daily usage guide (English) |
| [docs/ANLEITUNG.md](docs/ANLEITUNG.md) | Vollständige Anleitung (German) |
| [docs/LIMITS.md](docs/LIMITS.md) | What the project can and cannot do (English) |
| [docs/GRENZEN.md](docs/GRENZEN.md) | Was geht / was nicht (German) |
| [docs/WINDOWS-FIREWALL.md](docs/WINDOWS-FIREWALL.md) | Optional firewall allow-list |

---

## Contributing / License

Pull requests welcome (tests, allow-list updates, Linux firewall examples).  
License: **MIT** — see [LICENSE](LICENSE).

---

## Disclaimer

Not affiliated with xAI. Unofficial. Use at your own risk.  
xAI, Grok and related marks belong to their respective owners.
