#!/usr/bin/env python3
"""
SessionStart: warnt (stdout), wenn Filter-Proxy nicht erreichbar ist.
Versucht einmal ensure_proxy, blockiert die Session NICHT (fail-open fuer Arbeit).
"""
from __future__ import annotations

import json
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

HOST, PORT = "127.0.0.1", 18743


def port_open() -> bool:
    s = socket.socket()
    s.settimeout(0.4)
    try:
        s.connect((HOST, PORT))
        return True
    except OSError:
        return False
    finally:
        try:
            s.close()
        except OSError:
            pass


def health() -> bool:
    try:
        with urllib.request.urlopen(f"http://{HOST}:{PORT}/_gpf/health", timeout=1.5) as r:
            return r.status == 200
    except Exception:
        return False


def storage_filter() -> bool:
    try:
        urllib.request.urlopen(f"http://{HOST}:{PORT}/v1/storage", timeout=1.5)
        return False
    except urllib.error.HTTPError as e:
        return e.code == 403
    except Exception:
        return False


def main() -> int:
    # SessionStart hooks: print goes to scrollback / logs
    ok = port_open() and (health() or storage_filter())
    if ok:
        print("[grok-privacy-filter] Proxy OK (filter aktiv)")
        return 0

    ensure = Path.home() / ".grok" / "proxy" / "ensure_proxy.py"
    if ensure.is_file():
        try:
            subprocess.run(
                [sys.executable, str(ensure)],
                timeout=12,
                capture_output=True,
                text=True,
            )
        except Exception:
            pass

    ok2 = port_open() and (health() or storage_filter())
    if ok2:
        print("[grok-privacy-filter] Proxy war down — gestartet. Filter aktiv.")
        return 0

    print(
        "[grok-privacy-filter] WARNUNG: Filter-Proxy nicht erreichbar auf "
        f"{HOST}:{PORT}. Chat kann scheitern wenn cli_chat_proxy_base_url gesetzt ist. "
        "Fix: py -3 %USERPROFILE%\\.grok\\proxy\\ensure_proxy.py"
    )
    # fail-open: Session nicht killen
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
