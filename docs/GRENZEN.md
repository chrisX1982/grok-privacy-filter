# Grenzen — was dieses Projekt kann und was nicht

Bitte dieses Dokument **lesen**, bevor du Sicherheit oder „DSGVO-Erledigt“ behauptest.

## Kann

| Massnahme | Wirkung |
|-----------|---------|
| Privacy Opt-out API | `codingDataRetentionOptOut=true` am Konto |
| Config-Härtung | Telemetry/Trace/Feedback/Indexing/Remote-Prefetch ab |
| PreToolUse-Hook | Agent darf nicht per Shell/Web-Tool zu xAI/GCS pushen |
| Filter-Proxy | Auf dem Chat-Proxy-Host: nur erlaubte Pfade, Storage **403** |
| Optional Firewall | Host-Allowlist: nur Auth + lokaler Proxy |

## Kann nicht

| Wunsch | Realität |
|--------|----------|
| 100 % keine Daten an xAI bei laufendem Grok | **Unmöglich** — Inference **braucht** den Proxy |
| Physische Löschung aller Server-Kopien beweisen | **Nur xAI** (Privacy-Portal / Recht) |
| Frühere Git-Bundle-Uploads rückgängig machen | Opt-out + xAI-Aussagen; **nicht verifizierbar** von aussen |
| Hook stoppt `grok.exe`-Start-Upload | **Nein** — Binary-intern, kein Tool-Event |
| Proxy filtert `storage.googleapis.com` | **Nein** — anderer Host (Firewall extra) |

## Architektur (warum Firewall ≠ „Grok ohne Netz“)

```
┌─────────────┐     Chat/Tools      ┌──────────────────┐
│  grok.exe   │ ──────────────────► │ cli-chat-proxy   │  ← Produkt
└─────────────┘                     └──────────────────┘
       │
       │  optional früher / parallel
       ▼
┌─────────────────────┐
│ storage.googleapis  │  ← Codebase-Upload-Skandal-Pfad
└─────────────────────┘
```

- **Alles blocken** (Firewall auf grok.exe) → CLI tot.  
- **Filter-Proxy** → CLI lebt, Upload-Pfade auf dem Chat-Host sterben.  
- **Firewall nur GCS + Telemetry-Hosts** → sinnvoll **zusätzlich** zum Proxy.

## Rechtliches (keine Rechtsberatung)

Dieses Repo ist ein **Community-Schutz-Tool**. Es:

- ersetzt **keine** formelle Datenschutz-Anfrage an xAI,
- garantiert **keine** DSGVO-/AI-Act-Konformität von xAI,
- dokumentiert technische Kontrollen, die **du** auf deinem Rechner setzen kannst.

Offizielle Kanäle (Stand öffentlich bekannt):

- https://x.ai/privacy-portal  
- https://x.ai/legal/privacy-policy  
- privacy@x.ai  

## Versionen

Grok Build ändert Endpunkte und Flags. Nach Updates:

1. `scripts/verify.ps1` bzw. Hook-Tests  
2. Proxy-Logs auf unerwartete 403 bei normalem Chat prüfen  
3. Allowlist in `proxy/xai_filter_proxy.py` anpassen falls nötig  
