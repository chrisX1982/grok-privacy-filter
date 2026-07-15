# Grok Privacy Filter — VS Code / Cursor Extension

Für alle, die **nicht** die Terminal-TUI nutzen, sondern **Grok Build in VS Code** (oder Cursor) wie im Chat-Panel.

---

## Wichtig: Kein extra CMD-Fenster nötig

| Mythos | Realität |
|--------|----------|
| „Neues CMD starten“ | Nur für die **Terminal-TUI** (`grok` im Terminal). |
| **VS Code Extension** | Liest **`~/.grok/config.toml`**. Proxy muss im **Hintergrund** laufen. |

Der Filter greift in der Extension, wenn:

1. **`[endpoints] cli_chat_proxy_base_url`** auf den lokalen Proxy zeigt, und  
2. der **Proxy auf Port 18743** läuft, und  
3. du eine **neue Session** startest (`/new` oder Fenster neu laden) — alte Sessions behalten oft die alte Upstream-URL.

---

## Einmal einrichten (Windows)

Aus dem Repo-Root:

```powershell
# Basis (Hook, Proxy-Dateien, …)
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1

# Server Opt-out
py -3 .\config\privacy-opt-out.py

# VS Code: Config + Workspace-Task + Proxy jetzt starten
powershell -ExecutionPolicy Bypass -File .\scripts\install_vscode.ps1 -Workspace "C:\Pfad\zu\deinem\Projekt" -UserSettings

# Proxy bei Windows-Login immer sicherstellen
powershell -ExecutionPolicy Bypass -File .\scripts\install_autostart.ps1
```

**Aktuelles Projekt (z. B. dieses Repo geöffnet):**

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_vscode.ps1 -Workspace . -UserSettings
```

### Was `install_vscode.ps1` macht

| Aktion | Detail |
|--------|--------|
| Proxy-Dateien | nach `~/.grok/proxy/` (inkl. `ensure_proxy.py`) |
| Config | setzt/ergänzt `cli_chat_proxy_base_url = "http://127.0.0.1:18743/v1"` |
| `.vscode/tasks.json` | Task **„Grok Privacy: Ensure Filter Proxy“** mit `runOn: folderOpen` |
| `-UserSettings` | setzt `task.allowAutomaticTasks: "on"` in Code/Cursor User-Settings (Backup `.gpf-backup`) |
| Sofort | ruft `ensure_proxy.py` auf |

### Was `install_autostart.ps1` macht

| Aktion | Detail |
|--------|--------|
| Startup-Ordner | `GrokPrivacyFilterProxy.vbs` (unsichtbar, ruft `ensure_proxy.py`) |
| `-ScheduledTask` | zusätzlich geplante Aufgabe „At logon“ |
| `-Remove` | Autostart wieder entfernen |

---

## Jeden Tag (nach dem Einrichten)

1. **PC an** → Autostart startet den Proxy (falls installiert).  
2. **VS Code öffnen** → beim Ordner-Öffnen läuft die Task erneut (falls erlaubt) und startet den Proxy nur, wenn er **nicht** schon läuft.  
3. **Grok Extension** → normal chatten.  
4. Nach Config-Änderung: **`/new`** oder **Reload Window**.

Manuell Proxy erzwingen:

```powershell
py -3 $env:USERPROFILE\.grok\proxy\ensure_proxy.py
```

---

## Config (Kern für die Extension)

In `~/.grok/config.toml`:

```toml
[endpoints]
cli_chat_proxy_base_url = "http://127.0.0.1:18743/v1"
```

Das ist der Schalter, den **CLI und Extension** für den Chat-Proxy nutzen.  
Ohne laufenden Proxy: Verbindungen schlagen fehl (Port zu) — dann `ensure_proxy.py`.

Weitere Härtung: `config/config.snippet.toml` (Telemetry aus, …).

---

## Hook in der Extension

Hooks liegen global unter `~/.grok/hooks/` und gelten auch in der Extension.

- Install: `install.ps1`  
- Prüfen: in Grok **`/hooks`** → Reload **`r`** → `block-xai-upload`  
- Der Hook blockiert **Agent-Tools** (curl zu xAI etc.), **nicht** den internen Chat-Pfad (dafür der Proxy).

---

## Automatische Tasks in VS Code

Beim ersten `folderOpen` kann VS Code fragen, ob Tasks erlaubt sind.

- Erlauben, **oder**
- User-Setting: `"task.allowAutomaticTasks": "on"` (setzt `-UserSettings`)

Task manuell: **Terminal → Run Task… → „Grok Privacy: Ensure Filter Proxy“**.

Vorlage im Repo: `vscode/tasks.json` (kannst du nach `.vscode/tasks.json` kopieren).

---

## Cursor

Gleiche Mechanismen (`~/.grok/`, Tasks, `ensure_proxy`).  
`-UserSettings` schreibt auch nach `%APPDATA%\Cursor\User\settings.json`, falls vorhanden.

---

## Troubleshooting (Extension)

| Symptom | Ursache / Fix |
|---------|----------------|
| Chat geht gar nicht | Proxy aus → `ensure_proxy.py`; Port 18743 belegt von anderem Prozess? |
| Chat geht, aber „ungefiltert“? | Alte Session → `/new`; `cli_chat_proxy_base_url` in config prüfen |
| Task startet nie | `task.allowAutomaticTasks`; Trust des Workspace |
| Hook fehlt | `install.ps1`, dann `/hooks` → r |
| Nach Reboot tot | `install_autostart.ps1` nachholen |
| tasks.json überschrieben | Backup: `.vscode/tasks.json.gpf-backup` |

Logs Proxy:

- `~/.grok/proxy/logs/ensure-proxy-daemon.log`  
- `~/.grok/proxy/logs/proxy-YYYY-MM-DD.log` (wenn Proxy selbst loggt)  
- Repo: `logs/proxy-*.log` falls aus Repo gestartet  

---

## Abgrenzung Terminal-TUI

| Startart | Brauchst du |
|----------|-------------|
| **VS Code Extension** (dieses Doc) | `config.toml` endpoints + `ensure_proxy` / Autostart / folderOpen-Task |
| **Terminal `grok`** | optional `start_grok_filtered.cmd` **oder** dieselbe `config.toml` endpoints |

Mit gesetzter `cli_chat_proxy_base_url` in der Config brauchst du **kein** `GROK_CLI_CHAT_PROXY_BASE_URL` in der Environment — gilt für CLI und Extension.

---

## Verwandte Docs

- [ANLEITUNG.md](ANLEITUNG.md) — Gesamtablauf  
- [GRENZEN.md](GRENZEN.md) — was der Proxy nicht kann  
- [WINDOWS-FIREWALL.md](WINDOWS-FIREWALL.md) — optionale Host-Sperren  
