#!/usr/bin/env python3
"""Stoppt Listener auf Port 18743 und startet aktuellen Proxy neu (Windows/Unix)."""
from __future__ import annotations

import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

PORT = 18743


def pids_on_port(port: int) -> set[int]:
    pids: set[int] = set()
    try:
        out = subprocess.check_output(
            ["netstat", "-ano", "-p", "tcp"], text=True, errors="replace"
        )
    except Exception:
        return pids
    for line in out.splitlines():
        if f":{port}" not in line:
            continue
        # LISTENING / ABHÖREN / etc.
        if not re.search(r"LISTEN|ABH", line, re.I):
            continue
        parts = line.split()
        if not parts:
            continue
        try:
            pids.add(int(parts[-1]))
        except ValueError:
            pass
    return pids


def main() -> int:
    for pid in pids_on_port(PORT):
        if pid <= 0:
            continue
        print(f"stopping pid {pid}")
        if sys.platform.startswith("win"):
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
        else:
            subprocess.run(["kill", str(pid)], capture_output=True)
    time.sleep(1)

    ensure = Path.home() / ".grok" / "proxy" / "ensure_proxy.py"
    if not ensure.is_file():
        ensure = Path(__file__).resolve().parent / "ensure_proxy.py"
    r = subprocess.run([sys.executable, str(ensure), "-v"])
    time.sleep(0.5)
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{PORT}/v1/storage", timeout=3)
    except urllib.error.HTTPError as e:
        print("storage", e.code)
    try:
        h = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/_gpf/health", timeout=3)
        print("health", h.read().decode())
    except Exception as e:
        print("health fail", e)
        return 1
    return r.returncode or 0


if __name__ == "__main__":
    raise SystemExit(main())
