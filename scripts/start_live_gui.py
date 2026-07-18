#!/usr/bin/env python3
"""
Cross-platform launcher for the Grok Privacy Filter Live GUI.

Usage:
  python scripts/start_live_gui.py
  # or after install: python ~/.grok/proxy/start_live_gui.py

It will try to exec the installed live_proxy_gui.py if present,
otherwise fall back to the one next to this script (dev mode).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
import subprocess

def main() -> int:
    grok_proxy = Path.home() / ".grok" / "proxy"
    candidates = [
        grok_proxy / "live_proxy_gui.py",
        Path(__file__).resolve().parent.parent / "proxy" / "live_proxy_gui.py",
    ]

    gui = None
    for c in candidates:
        if c.is_file():
            gui = c
            break

    if not gui:
        print("FEHLER: live_proxy_gui.py nicht gefunden.", file=sys.stderr)
        print("Bitte installieren oder aus dem Repo starten.", file=sys.stderr)
        return 1

    # Use the same python that runs us
    cmd = [sys.executable, str(gui)]
    print(f"Starting GUI: {cmd}")
    try:
        # On Windows we let it inherit console flags etc.
        if os.name == "nt":
            return subprocess.call(cmd)
        else:
            os.execv(sys.executable, [sys.executable] + cmd[1:])
    except Exception as exc:
        print(f"Fehler beim Starten der GUI: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
