# Limits — what this project can and cannot do

Please **read** this document before claiming security or "GDPR done".

## Can

| Measure | Effect |
|---------|--------|
| Privacy Opt-out API | Sets `codingDataRetentionOptOut=true` on the account |
| Config hardening | Disables telemetry/trace/feedback/indexing/remote-prefetch |
| PreToolUse hook | Agent cannot push via shell/web tools to xAI/GCS |
| Filter proxy | On the chat proxy host: only allowed paths; storage returns **403** |
| Optional firewall | Host allow-list: only auth + local proxy |

## Cannot

| Wish | Reality |
|------|---------|
| 100% no data to xAI while Grok is running | **Impossible** — inference **requires** the proxy |
| Prove physical deletion of all server copies | **Only xAI** can do that (Privacy Portal / legal) |
| Undo previous Git bundle uploads | Opt-out + xAI statements; **not verifiable** from the outside |
| Hook stops `grok.exe` startup upload | **No** — internal to the binary, no tool event |
| Proxy filters `storage.googleapis.com` | **No** — different host (firewall separately) |

## Architecture (why firewall ≠ "Grok without network")

```
┌─────────────┐     Chat/Tools      ┌──────────────────┐
│  grok.exe   │ ──────────────────► │ cli-chat-proxy   │  ← Product
└─────────────┘                     └──────────────────┘
       │
       │  optional earlier / parallel
       ▼
┌─────────────────────┐
│ storage.googleapis  │  ← Codebase upload scandal path
└─────────────────────┘
```

- **Block everything** (firewall on grok.exe) → CLI is dead.
- **Filter proxy** → CLI lives, upload paths on the chat host die.
- **Firewall only for GCS + telemetry hosts** → makes sense **in addition** to the proxy.

## Legal (not legal advice)

This repository is a **community protection tool**. It:

- does **not** replace a formal data protection request to xAI,
- does **not** guarantee DSGVO / AI Act compliance by xAI,
- documents technical controls **you** can set on your machine.

Official channels (publicly known at time of writing):

- https://x.ai/privacy-portal  
- https://x.ai/legal/privacy-policy  
- privacy@x.ai  

## Versions

Grok Build changes endpoints and flags. After updates:

1. Run `scripts/verify.ps1` or hook tests
2. Check proxy logs for unexpected 403s on normal chat
3. Adjust allow list in `proxy/xai_filter_proxy.py` if necessary
