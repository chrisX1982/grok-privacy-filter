#!/usr/bin/env python3
"""
Setzt codingDataRetentionOptOut=true auf dem xAI-Konto (cli-chat-proxy API).

Liest den Token aus ~/.grok/auth.json (nach `grok login`).
Loescht KEINE lokalen Dateien.

Nutzung:
  python config/privacy-opt-out.py
  python config/privacy-opt-out.py --status
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

AUTH_PATH = Path.home() / ".grok" / "auth.json"
BASE = "https://cli-chat-proxy.grok.com/v1"
UA = "grok-privacy-filter/1.0"


def _load_token() -> tuple[str, dict]:
    if not AUTH_PATH.is_file():
        print(f"FEHLER: {AUTH_PATH} nicht gefunden. Zuerst: grok login", file=sys.stderr)
        sys.exit(1)
    data = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
    # auth.json: { "<issuer::client>": { key, email, coding_data_retention_opt_out, ... } }
    if not isinstance(data, dict) or not data:
        print("FEHLER: auth.json leer/ungueltig", file=sys.stderr)
        sys.exit(1)
    entry = next(iter(data.values()))
    token = entry.get("key")
    if not token:
        print("FEHLER: kein Token in auth.json", file=sys.stderr)
        sys.exit(1)
    return token, entry


def _request(method: str, url: str, token: str, body: dict | None = None) -> tuple[int, str]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": UA,
            "x-grok-client-version": "0.2.101",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return int(resp.status), resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return int(e.code), e.read().decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser(description="xAI coding data retention opt-out")
    ap.add_argument("--status", action="store_true", help="Nur Status anzeigen")
    args = ap.parse_args()

    token, entry = _load_token()
    print(f"Konto (lokal): {entry.get('email', '?')}")
    print(f"Lokal coding_data_retention_opt_out: {entry.get('coding_data_retention_opt_out')}")

    code, text = _request("GET", f"{BASE}/user", token)
    print(f"GET /v1/user -> {code}")
    print(text[:800])

    if args.status:
        return 0 if code == 200 else 1

    code2, text2 = _request(
        "PUT",
        f"{BASE}/privacy/coding-data-retention",
        token,
        {"codingDataRetentionOptOut": True},
    )
    print(f"PUT /v1/privacy/coding-data-retention -> {code2}")
    print(text2)

    code3, text3 = _request("GET", f"{BASE}/user", token)
    print(f"GET /v1/user (nachher) -> {code3}")
    print(text3[:800])

    if code2 == 200 and "true" in text2.lower():
        print("\nOK: codingDataRetentionOptOut=true serverseitig gesetzt.")
        print("Hinweis: Vollstaendige Datenloeschung nur xAI (privacy-portal).")
        return 0
    print("\nFEHLER: Opt-out konnte nicht bestaetigt werden.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
