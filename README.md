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
| 2 | `config/config.snippet.toml` | Telemetry/Trace/Prefetch/Indexing aus |
| 3 | `hooks/block-xai-upload.*` | Agent-Tools dürfen nicht zu xAI/GCS pushen |
| 4 | `proxy/xai_filter_proxy.py` | Nur erlaubte Pfade → Upstream; Storage **403** |
| 5 | (optional) Firewall | Nur Auth + lokaler Proxy — siehe Docs |

**Kein Marketing:** Firewall auf die ganze `grok.exe` = CLI tot.  
**Proxy** = CLI nutzbar + Upload-Pfade auf dem Chat-Host blocken.

---

## Schnellstart (5 Minuten)

### Voraussetzungen

- Grok Build installiert und einmal `grok login`
- Python **3.10+** (`python` / `python3` / Windows `py -3`)

### Windows

```powershell
git clone https://github.com/chrisX1982/grok-privacy-filter.git
cd grok-privacy-filter
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
py -3 .\config\privacy-opt-out.py
```

**Terminal 1:**

```bat
scripts\start_proxy.cmd
```

**Terminal 2:**

```bat
scripts\start_grok_filtered.cmd
```

### macOS / Linux

```bash
git clone https://github.com/chrisX1982/grok-privacy-filter.git
cd grok-privacy-filter
bash scripts/install.sh
python3 config/privacy-opt-out.py
# Terminal 1:
bash scripts/start_proxy.sh
# Terminal 2:
bash scripts/start_grok_filtered.sh
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
├── README.md                 ← du bist hier
├── LICENSE                   ← MIT
├── config/
│   ├── config.snippet.toml   ← in ~/.grok/config.toml mergen
│   └── privacy-opt-out.py    ← Server Opt-out
├── docs/
│   ├── ANLEITUNG.md          ← ausführlich, Schritt für Schritt
│   ├── GRENZEN.md            ← ehrliche Limits
│   └── WINDOWS-FIREWALL.md   ← optionale Host-Allowlist
├── hooks/
│   ├── block-xai-upload.py
│   └── block-xai-upload.json.template
├── proxy/
│   └── xai_filter_proxy.py   ← Default-Deny Reverse-Proxy
└── scripts/
    ├── install.ps1 / install.sh
    ├── start_proxy.cmd / .sh
    ├── start_grok_filtered.cmd / .sh
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
