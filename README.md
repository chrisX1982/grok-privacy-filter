# Grok Privacy Filter

**Community-Schutzmassnahmen** für die [Grok Build CLI](https://x.ai) (xAI):  
weniger unnötige Uploads, Coding-Data-Retention **Opt-out**, Agent-Hook, lokaler **Default-Deny-Proxy**.

> **English (short):** Local tools to harden Grok Build: server-side coding-data retention opt-out, config lockdown, PreToolUse hook against agent uploads, and a path-filtering reverse proxy in front of `cli-chat-proxy.grok.com`. This does **not** stop chat inference (product needs it) and does **not** prove server-side deletion. Full guide: [`docs/ANLEITUNG.md`](docs/ANLEITUNG.md) · Limits: [`docs/GRENZEN.md`](docs/GRENZEN.md).

---

## Warum das existiert

Im Juli 2026 wurde öffentlich dokumentiert, dass Grok Build u. a. **Repository-Inhalte** (Git-Bundle) an Cloud-Storage senden konnte — unabhängig davon, welche Dateien der Agent „gelesen“ hat. xAI verwies u. a. auf **`/privacy`**, ZDR (Enterprise) und spätere Server-Flags.

Dieses Repo bündelt **sofort nutzbare** Gegenmassnahmen für Einzelpersonen:

| Schicht | Werkzeug | Wirkung |
|--------|----------|---------|
| 1 | `config/privacy-opt-out.py` | API: `codingDataRetentionOptOut=true` |
| 2 | `config/config.snippet.toml` | Telemetry/Trace/Prefetch/Indexing + **endpoints-Proxy** |
| 3 | `hooks/block-xai-upload.*` | Agent-Tools dürfen nicht zu xAI/GCS pushen |
| 4 | `proxy/xai_filter_proxy.py` + `ensure_proxy.py` | Default-Deny-Proxy; startet nur wenn nötig |
| 5 | Autostart / VS Code Task | Proxy bei Login bzw. beim Öffnen des Workspace |
| 6 | (optional) Firewall | Nur Auth + lokaler Proxy — siehe Docs |

**VS Code Extension:** Kein extra CMD — Config `cli_chat_proxy_base_url` + Hintergrund-Proxy.  
Details: **[docs/VSCODE.md](docs/VSCODE.md)**.

**Kein Marketing:** Firewall auf die ganze `grok.exe` = CLI tot.  
**Proxy** = CLI/Extension nutzbar + Upload-Pfade auf dem Chat-Host blocken.

---

## Schnellstart (5 Minuten)

### Voraussetzungen

- Grok Build installiert und einmal `grok login`
- Python **3.10+** (`python` / `python3` / Windows `py -3`)

### Windows — empfohlen wenn du in **VS Code** arbeitest

```powershell
git clone https://github.com/chrisX1982/grok-privacy-filter.git
cd grok-privacy-filter
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
py -3 .\config\privacy-opt-out.py
powershell -ExecutionPolicy Bypass -File .\scripts\install_vscode.ps1 -Workspace "C:\Pfad\zu\deinem\Projekt" -UserSettings
powershell -ExecutionPolicy Bypass -File .\scripts\install_autostart.ps1
```

Danach in Grok: **`/new`** (oder VS Code Window Reload).

| Script | Zweck |
|--------|--------|
| `install.ps1` | Hook, Proxy-Dateien, Config-Hinweis |
| `install_vscode.ps1` | `endpoints` in config + Task beim Ordner-Öffnen |
| `install_autostart.ps1` | Proxy bei Windows-Login (unsichtbar) |
| `ensure_proxy.py` | Proxy starten **nur wenn** Port 18743 frei/zu |

### Windows — nur Terminal-TUI (optional)

```bat
scripts\start_proxy.cmd
scripts\start_grok_filtered.cmd
```

Mit `cli_chat_proxy_base_url` in der Config reicht oft nur `ensure_proxy` + normales `grok`.

### macOS / Linux

```bash
git clone https://github.com/chrisX1982/grok-privacy-filter.git
cd grok-privacy-filter
bash scripts/install.sh
python3 config/privacy-opt-out.py
bash scripts/install_autostart.sh
python3 ~/.grok/proxy/ensure_proxy.py
# VS Code: docs/VSCODE.md — vscode/tasks.json nach .vscode/ kopieren
```

### Prüfen

```powershell
# Windows
powershell -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

```bash
curl -i http://127.0.0.1:18743/v1/storage   # erwartet: 403
curl -i http://127.0.0.1:18743/v1/models    # Upstream (z.B. 401 ohne Token = OK)
```

In Grok: `/hooks` → Reload → **block-xai-upload** aktiv.

---

## Ordnerstruktur

```text
grok-privacy-filter/
├── README.md
├── LICENSE
├── config/
│   ├── config.snippet.toml      ← inkl. [endpoints] Proxy-URL
│   └── privacy-opt-out.py
├── docs/
│   ├── ANLEITUNG.md
│   ├── VSCODE.md                ← Extension-Alltag (kein CMD)
│   ├── GRENZEN.md
│   ├── WINDOWS-FIREWALL.md
│   └── GITHUB.md
├── hooks/
├── proxy/
│   └── xai_filter_proxy.py
├── vscode/
│   └── tasks.json               ← Vorlage folderOpen → ensure_proxy
└── scripts/
    ├── install.ps1 / install.sh
    ├── install_vscode.ps1       ← Config + Workspace-Task
    ├── install_autostart.ps1/.sh
    ├── ensure_proxy.py          ← startet Proxy nur wenn noetig
    ├── start_proxy.* / start_grok_filtered.*
    └── verify.ps1
```

---

## Proxy: Allow / Deny (Kernlogik)

**Allow (Prefix):**

- `/v1/chat/completions`, `/v1/responses`
- `/v1/models`, `/v1/user`
- `/v1/privacy/coding-data-retention`
- `/v1/settings` — **nur GET**

**Deny:**

- `/v1/storage`, Upload/Sync/Trace/Telemetry-Pfade  
- **alles andere** (default-deny)  
- Heuristik: Git-PACK / Bundle-Signaturen im Body  

Upstream: `https://cli-chat-proxy.grok.com`  
Lokal: `http://127.0.0.1:18743`  
Env: `GROK_CLI_CHAT_PROXY_BASE_URL=http://127.0.0.1:18743/v1`

---

## Wichtige CLI-Fakten

| Befehl | Bedeutung |
|--------|-----------|
| `/privacy opt-out` | Privacy-Modus (Retention/Share aus) |
| `/privacy opt-in` | Daten teilen |
| nur `/privacy` | oft **leere UI** — Argument nötig |

API (mit Session-Token aus `~/.grok/auth.json`):

```http
PUT https://cli-chat-proxy.grok.com/v1/privacy/coding-data-retention
{"codingDataRetentionOptOut": true}
```

Formelle Löschung bei xAI: [privacy-portal](https://x.ai/privacy-portal) — **nicht** Teil dieses Tools.

---

## Sicherheitshinweise

- **Niemals** `auth.json`, API-Keys oder Session-Tokens committen.  
- Opt-out und Proxy sind **keine** Rechtsberatung und **kein** Beweis der Server-Löschung.  
- Nach Grok-Updates Allowlist und Tests erneut laufen lassen.  
- Secrets, die je im Repo lagen: **rotieren**.

---

## Dokumentation

| Datei | Inhalt |
|-------|--------|
| [docs/VSCODE.md](docs/VSCODE.md) | **VS Code / Cursor Extension** — Autostart, Tasks, Config |
| [docs/ANLEITUNG.md](docs/ANLEITUNG.md) | Vollständige Installations- und Alltagsanleitung |
| [docs/GRENZEN.md](docs/GRENZEN.md) | Was geht / was nicht |
| [docs/WINDOWS-FIREWALL.md](docs/WINDOWS-FIREWALL.md) | Optionale Firewall-Allowlist |

---

## Mitwirken / Lizenz

Pull Requests willkommen (Tests, Allowlist-Updates, Linux-Firewall-Beispiele).  
Lizenz: **MIT** — siehe [LICENSE](LICENSE).

---

## Disclaimer

Nicht von xAI. Unofficial. Use at your own risk.  
xAI, Grok und zugehörige Marken gehören den jeweiligen Inhabern.
