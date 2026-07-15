#!/usr/bin/env python3
"""
Stellt sicher, dass der xAI-Filter-Proxy lauscht (Default 127.0.0.1:18743).

- Laeuft er schon? → Exit 0, nichts tun.
- Laeuft er nicht? → startet xai_filter_proxy.py im Hintergrund (ohne Konsole unter Windows).

Aufruf:
  python scripts/ensure_proxy.py
  python scripts/ensure_proxy.py --port 18743 --verbose

Exit-Codes:
  0 = Proxy erreichbar (war schon an oder wurde gestartet)
  1 = Start fehlgeschlagen
"""
from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 18743


def _pkg_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _candidate_scripts() -> list[Path]:
    home = Path.home() / ".grok" / "proxy" / "xai_filter_proxy.py"
    repo = _pkg_root() / "proxy" / "xai_filter_proxy.py"
    # Installierte Kopie zuerst (stabiler Pfad nach install.ps1)
    return [p for p in (home, repo) if p.is_file()]


def port_open(host: str, port: int, timeout: float = 0.4) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        try:
            s.close()
        except OSError:
            pass


def start_proxy(script: Path, host: str, port: int, verbose: bool) -> subprocess.Popen:
    log_dir = Path.home() / ".grok" / "proxy" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "ensure-proxy-daemon.log"
    logf = open(log_path, "a", encoding="utf-8")
    logf.write(f"\n--- ensure_proxy start {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
    logf.flush()

    cmd = [
        sys.executable,
        str(script),
        "--bind",
        host,
        "--port",
        str(port),
    ]
    kwargs: dict = {
        "stdout": logf,
        "stderr": subprocess.STDOUT,
        "cwd": str(script.parent),
    }
    if os.name == "nt":
        # Kein Konsolenfenster
        CREATE_NO_WINDOW = 0x08000000
        DETACHED_PROCESS = 0x00000008
        kwargs["creationflags"] = CREATE_NO_WINDOW | DETACHED_PROCESS
        kwargs["close_fds"] = True
    else:
        kwargs["start_new_session"] = True

    if verbose:
        print(f"Starting: {' '.join(cmd)}", file=sys.stderr)
        print(f"Log: {log_path}", file=sys.stderr)

    return subprocess.Popen(cmd, **kwargs)


def main() -> int:
    ap = argparse.ArgumentParser(description="Ensure xAI filter proxy is running")
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--wait-secs", type=float, default=5.0)
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    if port_open(args.host, args.port):
        if args.verbose:
            print(f"OK: Proxy already on {args.host}:{args.port}")
        else:
            print(f"proxy already running on {args.host}:{args.port}")
        return 0

    scripts = _candidate_scripts()
    if not scripts:
        print(
            "FEHLER: xai_filter_proxy.py nicht gefunden "
            "(weder ~/.grok/proxy noch Repo proxy/). Zuerst install.ps1 / install.sh.",
            file=sys.stderr,
        )
        return 1

    script = scripts[0]
    if args.verbose:
        print(f"Proxy down — starting {script}", file=sys.stderr)

    try:
        start_proxy(script, args.host, args.port, args.verbose)
    except Exception as exc:
        print(f"FEHLER beim Start: {exc}", file=sys.stderr)
        return 1

    deadline = time.time() + args.wait_secs
    while time.time() < deadline:
        if port_open(args.host, args.port):
            print(f"proxy started on {args.host}:{args.port}")
            return 0
        time.sleep(0.2)

    print(
        f"FEHLER: Proxy startete nicht innerhalb {args.wait_secs}s "
        f"(siehe ~/.grok/proxy/logs/ensure-proxy-daemon.log)",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
