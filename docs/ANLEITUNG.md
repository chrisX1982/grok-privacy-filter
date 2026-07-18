# Ausführliche Anleitung — Grok Privacy Filter

Schritt-für-Schritt für **Windows**, **macOS** und **Linux**.  
Voraussetzungen: **Grok Build CLI** installiert, **Python 3.10+**, Internetzugang.

---

## 0. Was du am Ende hast

1. **Server-Opt-out** — Konto will keine Coding-Data-Retention  
2. **Harte CLI-Config** — Telemetry/Trace/Prefetch aus + **`cli_chat_proxy_base_url`**  
3. **Hook** — Agent darf nicht zu xAI/GCS hochladen  
4. **Filter-Proxy** — Chat läuft, Storage/Upload-Pfade → **403**  
5. **ensure_proxy** — startet den Proxy nur, wenn er nicht läuft  
6. **Autostart und/oder VS Code folderOpen-Task**  
7. (Optional) **Firewall** — nur Auth + lokaler Proxy  

**Arbeitest du in der VS Code Extension?** → primär **[VSCODE.md](VSCODE.md)** lesen.  
Kein extra CMD-Fenster nötig.

Lies parallel: [GRENZEN.md](GRENZEN.md).

---

## 1. Repo holen

```bash
git clone https://github.com/chrisX1982/grok-privacy-filter.git
cd grok-privacy-filter
```

Oder ZIP von GitHub laden und entpacken.

---

## Schnellstart für die meisten Nutzer (5–10 Minuten)

**Ziel:** Mit nur wenigen Schritten vollen Datenschutz aktivieren. Die GUI ist der empfohlene Einstieg.

1. **Repo holen** (oben bereits getan)

2. **Einfachen Installer starten**
   - **Windows:**  
     `powershell -ExecutionPolicy Bypass -File .\scripts\install_easy.ps1`
   - **macOS / Linux:**  
     `bash scripts/install_easy.sh`

   → Die **Live-GUI** öffnet sich automatisch.

3. **In der GUI (einmalig)**
   - Klicke **„Empfohlene Datenschutz-Defaults“**
   - Klicke **„Proxy starten“**
   - Status zeigt: **DATENKLAU-SCHUTZ AKTIV ✓** + grüner Balken

4. **Loslegen**
   - In Grok einfach `/new` oder VS Code Window neu laden.
   - Danach immer über Desktop-Verknüpfung „Proxy Live Status“ starten.

**Fertig.** Du brauchst keine Configs oder Policy manuell zu editieren.

---

## Detaillierte Anleitung (für Fortgeschrittene)

Die folgenden Abschnitte sind die vollständige Anleitung mit allen Optionen, Hintergründen und manuellen Schritten.

## 2. Installation (detailliert)

### Windows (PowerShell) — Einfach (empfohlen)

```powershell
cd C:\Pfad\zu\grok-privacy-filter
powershell -ExecutionPolicy Bypass -File .\scripts\install_easy.ps1
```

Die Live-GUI öffnet sich. Verwende danach die Desktop-Verknüpfung.

### Windows — Vollständig (VS Code + Autostart)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_all.ps1 -Workspace "C:\Pfad\zu\deinem\Projekt"
```

### macOS / Linux — Einfach (empfohlen)

```bash
cd /pfad/zu/grok-privacy-filter
bash scripts/install_easy.sh
```

### Was der Installer macht

| Aktion | Ziel |
|--------|------|
| Hook kopieren | `~/.grok/hooks/block-xai-upload.py` + `.json` |
| Proxy kopieren | `~/.grok/proxy/` (Kopie) |
| Config | Snippet **nur** wenn noch keine `config.toml` existiert |

**Bestehende `~/.grok/config.toml` wird nicht überschrieben.**  
Dann manuell mergen: `config/config.snippet.toml`.

---

## 3. Privacy Opt-out (Server)

Du musst bei Grok eingeloggt sein (`grok login`), damit `~/.grok/auth.json` existiert.

```bash
# Windows
py -3 config\privacy-opt-out.py

# macOS/Linux
python3 config/privacy-opt-out.py
```

Erwartete Ausgabe u. a.:

```text
PUT /v1/privacy/coding-data-retention -> 200
{"codingDataRetentionOptOut":true}
```

Nur Status prüfen:

```bash
python3 config/privacy-opt-out.py --status
```

In der CLI (falls UI funktioniert):

```text
/privacy opt-out
```

(Nur `/privacy` ohne Argument zeigt oft **nichts** — Argument ist Pflicht.)

---

## 4. Config härten

Öffne `~/.grok/config.toml` und übernimm die Keys aus:

`config/config.snippet.toml`

Wichtigste Punkte:

- `telemetry = false`, `trace_upload = false`
- `feedback = false`
- `codebase_indexing = false`
- `remote_fetch = false` ← kein Remote-Prefetch (Trade-off: bundled Models)
- `harness.disable_codebase_upload = true`
- `memory.enabled = false`
- Permission-Deny-Liste für curl/iwr zu xAI-Hosts

Danach: **neue Grok-Session**.

---

## 5. Filter-Proxy + Live-GUI (empfohlen)

Die `live_proxy_gui.py` ist die zentrale, einfache Oberfläche:

- Proxy per Button starten/stoppen  
- Ein Häkchen „Datenklau-Schutz aktiv“ → blockiert **wirklich alles** was Datenklau ermöglicht (Storage, Codebase, Telemetrie, Feedback, Uploads, Bundles, Sync …)  
- Einstellungen direkt im Fenster (keine policy.json mehr von Hand)  
- Oben steht sofort „DATENKLAU-SCHUTZ AKTIV ✓“ + klare Liste der blockierten Kategorien

Start:
```powershell
python proxy\live_proxy_gui.py
```
Oder die Desktop-Verknüpfung (wird beim Install angelegt).

Danach in Grok einfach `/new`.

### 5b. VS Code + Autostart

Die install-Skripte richten weiterhin `ensure_proxy` + Task ein.  
Zusätzlich startest du einfach die GUI per Desktop-Shortcut.  
Du siehst dann live, ob der Datenklau-Schutz steht.

Kern in `~/.grok/config.toml`:
```toml
[endpoints]
cli_chat_proxy_base_url = "http://127.0.0.1:18743/v1"
```

### 5c. Terminal / Headless (optional)

```bat
scripts\start_proxy.cmd
scripts\start_proxy_silent.vbs   # Proxy unsichtbar, GUI sichtbar
```

**Für die meisten Nutzer reicht die Live-GUI.**  
Ein Schalter, Start per Button, sofort sichtbar dass Datenklau blockiert ist. Kein manuelles Edit von Prefixen nötig.

Logs: `~/.grok/proxy/logs/` und ggf. Repo `logs/`.

---

## 6. Hook aktivieren / prüfen

1. Grok starten  
2. `/hooks` öffnen  
3. **`r`** = Reload  
4. Eintrag **block-xai-upload** sichtbar und enabled  

Test im Chat (Agent soll z. B. ausführen):

```text
curl https://cli-chat-proxy.grok.com/v1/storage
```

Erwartung: Hook **deny**.

---

## 7. Verifikation

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

### Manuell Proxy

Mit laufendem Proxy:

```bash
# muss 403 sein
curl -i http://127.0.0.1:18743/v1/storage

# geht zum Upstream (oft 401 ohne Token — das ist OK)
curl -i http://127.0.0.1:18743/v1/models
```

---

## 8. Optional: Firewall

Siehe [WINDOWS-FIREWALL.md](WINDOWS-FIREWALL.md).

---

## 9. Datenlöschung bei xAI (nicht automatisierbar)

Technisch erreichbar von hier: **Opt-out + keine weiteren Uploads**.

Für formelle Löschung:

1. https://x.ai/privacy-portal  
2. Ggf. privacy@x.ai  
3. Secrets im Repo **rotieren**, falls sie je im Workspace lagen  

---

## 10. Alltags-Workflow (Empfehlung)

```text
1. Live-GUI starten (Desktop-Shortcut oder python proxy\live_proxy_gui.py)
2. Proxy-Button klicken (Datenklau-Schutz ist automatisch an)
3. Arbeiten
4. In der GUI siehst du sofort Status + Blocks
```

Die GUI ist die einfache, sichtbare Kontrolle. Kein manuelles Rumfummeln in Configs.

---

## 11. Deinstallation

```text
Löschen:
  ~/.grok/hooks/block-xai-upload.py
  ~/.grok/hooks/block-xai-upload.json
  ~/.grok/proxy/   (falls Kopie)

Config-Keys aus config.toml entfernen (Snippet-Teile)

Firewall-Regeln "Grok Privacy*" entfernen
```

Repo-Ordner kann bleiben oder gelöscht werden.

---

## 12. Troubleshooting

| Problem | Fix |
|---------|-----|
| Proxy startet nicht | Python 3.10+? Port 18743 frei? |
| Grok verbindet nicht | Proxy läuft? Env `GROK_CLI_CHAT_PROXY_BASE_URL` gesetzt? |
| Chat 403 | Allowlist zu eng — Log prüfen, Pfad in `ALLOW_PREFIXES` ergänzen |
| Hook läuft nicht | `/hooks` reload; Python-Pfad in JSON korrekt? |
| Opt-out 401 | Neu `grok login` |
| VS Code Extension | Env ggf. in der Extension/Terminal-Profile setzen |

---

## 13. Für GitHub-Maintainer

- Keine `auth.json` / Tokens committen (siehe `.gitignore`)  
- Nach Grok-Releases: `verify` + Allowlist prüfen  
- Issues: bitte Grok-Version (`grok version`), OS, Proxy-Log-Ausschnitt  
