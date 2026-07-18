# Detailed Instructions — Grok Privacy Filter

Step-by-step guide for **Windows**, **macOS**, and **Linux**.  
Prerequisites: **Grok Build CLI** installed, **Python 3.10+**, internet access.

---

## 0. What you will have at the end

1. **Server opt-out** — account requests no coding data retention
2. **Hardened CLI config** — telemetry/trace/prefetch/indexing disabled + **`cli_chat_proxy_base_url`**
3. **Hook** — agent may not upload to xAI/GCS
4. **Filter proxy** — chat works, storage/upload paths return **403**
5. **ensure_proxy** — starts the proxy only when it is not already running
6. **Autostart and/or VS Code folderOpen task**
7. (Optional) **Firewall** — only auth + local proxy allowed

**Working in the VS Code Extension?** → primarily read **[VSCODE.md](VSCODE.md)**.  
No extra command prompt window required.

Read in parallel: [LIMITS.md](LIMITS.md).

---

## 1. Clone the repository

```bash
git clone https://github.com/chrisX1982/grok-privacy-filter.git
cd grok-privacy-filter
```

Or download the ZIP from GitHub and extract it.

---

## Quick start for most users (5–10 minutes)

**Goal:** Activate full privacy protection with just a few steps. The GUI is the recommended way to get started.

1. **Clone the repo** (already done above)

2. **Run the easy installer**
   - **Windows:**  
     `powershell -ExecutionPolicy Bypass -File .\scripts\install_easy.ps1`
   - **macOS / Linux:**  
     `bash scripts/install_easy.sh`

   → The **Live GUI** opens automatically.

3. **In the GUI (one-time)**
   - Click **"Recommended Defaults"** or **"Full Start"** (recommended)
   - Go to menu **Actions → Check Hooks** (verifies installation)
   - Status should show: **PROTECTION ACTIVE ✓** + banner + status bar

4. **Get started**
   - In Grok: type `/hooks-trust` (trust the local hook)
   - Then open `/hooks` and press `r` to reload
   - Then `/new` or reload the VS Code window.
   - From now on always start via the desktop shortcut "Proxy Live Status".

**Done.**

Hooks are installed. In Grok enter `/hooks-trust`, then open `/hooks` and press `r`. You should now see the `block-xai-upload` entry under `/hooks`.

---

## Detailed instructions (for advanced users)

The following sections contain the complete guide with all options, background, and manual steps.

## 2. Installation (detailed)

### Windows (PowerShell) — Easy (recommended)

```powershell
cd C:\Path\to\grok-privacy-filter
powershell -ExecutionPolicy Bypass -File .\scripts\install_easy.ps1
```

The Live GUI opens. Use the desktop shortcut afterwards.

### Windows — Complete (VS Code + Autostart)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_all.ps1 -Workspace "C:\Path\to\your\project"
```

### macOS / Linux — Easy (recommended)

```bash
cd /path/to/grok-privacy-filter
bash scripts/install_easy.sh
```

### What the installer does

| Action | Target |
|--------|--------|
| Copy hook | `~/.grok/hooks/block-xai-upload.py` + `.json` |
| Copy proxy | `~/.grok/proxy/` (copy) |
| Config | Snippet **only** if no `config.toml` exists yet |

**Existing `~/.grok/config.toml` is never overwritten.**  
Merge manually if needed: `config/config.snippet.toml`.

---

## 3. Privacy Opt-out (server side)

You must be logged into Grok (`grok login`) so that `~/.grok/auth.json` exists.

```bash
# Windows
py -3 config\privacy-opt-out.py

# macOS/Linux
python3 config/privacy-opt-out.py
```

Expected output includes:

```text
PUT /v1/privacy/coding-data-retention -> 200
{"codingDataRetentionOptOut":true}
```

Check status only:

```bash
python3 config/privacy-opt-out.py --status
```

In the CLI (if the UI works):

```text
/privacy opt-out
```

(Just `/privacy` without an argument often shows **nothing** — the argument is required.)

---

## 4. Harden the config

Open `~/.grok/config.toml` and merge the keys from:

`config/config.snippet.toml`

Key points:

- `telemetry = false`, `trace_upload = false`
- `feedback = false`
- `codebase_indexing = false`
- `remote_fetch = false` ← no remote prefetch (trade-off: bundled models)
- `harness.disable_codebase_upload = true`
- `memory.enabled = false`
- Permission deny list for curl/iwr to xAI hosts

Afterwards: **start a new Grok session**.

---

## 5. Filter Proxy + Live GUI (recommended)

`live_proxy_gui.py` is the central, easy-to-use interface (bilingual DE/EN, switchable via "Language" menu):

- Menu bar (File, View, Actions, Help, Language)
- Top status lines (PROXY / PROTECTION), time, "Always on top"
- Colored banner with the block list
- Log with color highlighting
- Bottom direct buttons – Start Proxy, Stop Proxy, Recommended Defaults, Full Start, Advanced (switches mode + window size)
- Bottom status bar for feedback (including hook hints)
- Menu **Actions → Check Hooks**: verifies whether hook files are installed
- Settings only via menu (File → Settings...)
- Instant visual feedback; buttons are disabled when not usable

Start:
```powershell
python proxy\live_proxy_gui.py
```
Or use the desktop shortcut (created during install).

Then simply type `/new` in Grok.

### 5b. VS Code + Autostart

The install scripts still set up `ensure_proxy` + task.  
In addition you simply launch the GUI via desktop shortcut.  
You then see live whether the data exfiltration protection is in place.

Core setting in `~/.grok/config.toml`:
```toml
[endpoints]
cli_chat_proxy_base_url = "http://127.0.0.1:18743/v1"
```

### 5c. Terminal / Headless (optional)

```bat
scripts\start_proxy.cmd
scripts\start_proxy_silent.vbs   # proxy invisible, GUI visible
```

**For most users the Live GUI is sufficient.**  
Clear buttons + menu, instantly visible whether protection is active (banner + status). No manual editing of prefixes required.

Logs: `~/.grok/proxy/logs/` and possibly `logs/` in the repo.

---

## 6. Activate / verify the hook

1. Start Grok  
2. Type `/hooks-trust` (trust the local hook)  
3. Open `/hooks`  
4. Press **`r`** = Reload  
5. Entry **block-xai-upload** should be visible and enabled  

Test in chat (agent should e.g. execute):

```text
curl https://cli-chat-proxy.grok.com/v1/storage
```

Expected: Hook **denies**.

---

## 7. Verification

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

### Manual proxy test

With the proxy running:

```bash
# must return 403
curl -i http://127.0.0.1:18743/v1/storage

# reaches upstream (often 401 without token — this is OK)
curl -i http://127.0.0.1:18743/v1/models
```

---

## 8. Optional: Firewall

See [WINDOWS-FIREWALL.md](WINDOWS-FIREWALL.md).

---

## 9. Data deletion at xAI (not automatable here)

Technically achievable from here: **opt-out + no further uploads**.

For formal deletion:

1. https://x.ai/privacy-portal  
2. Possibly privacy@x.ai  
3. **Rotate** secrets that were ever in the workspace if they ever lived there

---

## 10. Daily workflow (recommendation)

```text
1. Start Live GUI (desktop shortcut or python proxy\live_proxy_gui.py)
2. "Full Start" or "Start Proxy" + "Recommended Defaults"
3. Work
4. In the GUI you immediately see status + blocks (banner + status bar)
```

The GUI is the simple, visible control. No manual fiddling with configs. Menu for everything else.

---

## 11. Uninstallation

```text
Delete:
  ~/.grok/hooks/block-xai-upload.py
  ~/.grok/hooks/block-xai-upload.json
  ~/.grok/proxy/   (if copied)

Remove config keys from config.toml (the snippet parts)

Remove firewall rules named "Grok Privacy*"
```

The repository folder can stay or be deleted.

---

## 12. Troubleshooting

| Problem | Fix |
|---------|-----|
| Proxy does not start | Python 3.10+? Port 18743 free? |
| Grok cannot connect | Is proxy running? Env `GROK_CLI_CHAT_PROXY_BASE_URL` set? |
| Chat returns 403 | Allow list too strict — check logs, add path to `ALLOW_PREFIXES` |
| Hook does not run | `/hooks-trust`; then `/hooks` → `r`; correct Python path in JSON? |
| Opt-out returns 401 | Run `grok login` again |
| VS Code Extension | Set env in the extension / terminal profile if needed |

---

## 13. For GitHub maintainers

- Never commit `auth.json` / tokens (see `.gitignore`)
- After Grok releases: run `verify` + review allow list
- When opening issues: please include Grok version (`grok version`), OS, and a snippet from the proxy log
