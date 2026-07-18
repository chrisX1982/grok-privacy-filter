# Publishing the repository on GitHub

## 1. Create a new repository

On GitHub: **New repository** → e.g. `grok-privacy-filter`  
**Do not** let the wizard create a README or License (they already exist in the folder).

## 2. Push locally

```bash
cd /path/to/grok-privacy-filter
git init
git add .
git status   # DO NOT include auth.json / tokens
git commit -m "Initial release: Grok privacy filter (proxy, hook, opt-out)"
git branch -M main
git remote add origin https://github.com/chrisX1982/grok-privacy-filter.git
git push -u origin main
```

## 3. Adjust README

Clone URL: `https://github.com/chrisX1982/grok-privacy-filter`

## 4. Repository description (suggestion)

```text
Local privacy hardening for xAI Grok Build CLI: retention opt-out, config lockdown, agent upload hook, default-deny filter proxy.
```

Topics: `grok`, `xai`, `privacy`, `security`, `cli`, `proxy`

## 5. Warning in the About section

Optional: "Unofficial · Not affiliated with xAI"

## 6. Releases

Create a tag e.g. `v1.0.0` with short text taken from `CHANGELOG.md`.
