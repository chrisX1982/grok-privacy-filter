# Repo auf GitHub veröffentlichen

## 1. Neues Repo anlegen

Auf GitHub: **New repository** → z. B. `grok-privacy-filter`  
**Keine** README/License vom Wizard (liegt schon im Ordner).

## 2. Lokal pushen

```bash
cd /pfad/zu/grok-privacy-filter
git init
git add .
git status   # KEINE auth.json / Tokens
git commit -m "Initial release: Grok privacy filter (proxy, hook, opt-out)"
git branch -M main
git remote add origin https://github.com/chrisX1982/grok-privacy-filter.git
git push -u origin main
```

## 3. README anpassen

Clone-URL: `https://github.com/chrisX1982/grok-privacy-filter`

## 4. Repo-Beschreibung (Vorschlag)

```text
Local privacy hardening for xAI Grok Build CLI: retention opt-out, config lockdown, agent upload hook, default-deny filter proxy.
```

Topics: `grok`, `xai`, `privacy`, `security`, `cli`, `proxy`

## 5. Warnhinweis im About

Optional: „Unofficial · Not affiliated with xAI“

## 6. Releases

Tag z. B. `v1.0.0` mit Kurztext aus `CHANGELOG.md`.
