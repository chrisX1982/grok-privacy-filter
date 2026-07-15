#!/usr/bin/env python3
"""
Stellt sicher, dass der xAI-Filter-Proxy lauscht und antwortet.

- Port offen + GET /_gpf/health = OK
- sonst start im Hintergrund (Windows: ohne Konsole)
- --watchdog: periodisch pruefen und neu starten

Exit: 0 OK, 1 Fehler
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 18743


def _pkg_root() -> Path:
    # scripts/ensure_proxy.py -> repo root; or ~/.grok/proxy/ensure_proxy.py -> parent is proxy dir
    p = Path(__file__).resolve().parent
    if (p / "xai_filter_proxy.py").is_file():
        return p  # installed under ~/.grok/proxy
    return p.parent


def _install_dir() -> Path:
    home = Path.home() / ".grok" / "proxy"
    if (home / "xai_filter_proxy.py").is_file():
        return home
    root = _pkg_root()
    if (root / "proxy" / "xai_filter_proxy.py").is_file():
        return root / "proxy"
    if (root / "xai_filter_proxy.py").is_file():
        return root
    return home


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


def health_ok(host: str, port: int, timeout: float = 2.0) -> bool:
    url = f"http://{host}:{port}/_gpf/health"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            if resp.status != 200:
                return False
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
            return bool(data.get("ok"))
    except Exception:
        return False


def start_proxy(install_dir: Path, host: str, port: int, verbose: bool) -> None:
    script = install_dir / "xai_filter_proxy.py"
    if not script.is_file():
        raise FileNotFoundError(str(script))

    log_dir = Path.home() / ".grok" / "proxy" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "ensure-proxy-daemon.log"
    logf = open(log_path, "a", encoding="utf-8")
    logf.write(f"\n--- ensure_proxy start {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
    logf.write(f"python={sys.executable}\n")
    logf.write(f"script={script}\n")
    logf.flush()

    policy = install_dir / "policy.json"
    cmd = [
        sys.executable,
        str(script),
        "--bind",
        host,
        "--port",
        str(port),
    ]
    if policy.is_file():
        cmd.extend(["--policy", str(policy)])

    kwargs: dict = {
        "stdout": logf,
        "stderr": subprocess.STDOUT,
        "cwd": str(install_dir),
    }
    if os.name == "nt":
        CREATE_NO_WINDOW = 0x08000000
        DETACHED_PROCESS = 0x00000008
        kwargs["creationflags"] = CREATE_NO_WINDOW | DETACHED_PROCESS
        kwargs["close_fds"] = True
    else:
        kwargs["start_new_session"] = True

    if verbose:
        print(f"Starting: {' '.join(cmd)}", file=sys.stderr)
        print(f"Log: {log_path}", file=sys.stderr)

    subprocess.Popen(cmd, **kwargs)


def ensure_once(host: str, port: int, wait_secs: float, verbose: bool) -> int:
    if port_open(host, port) and health_ok(host, port):
        if verbose:
            print(f"OK: healthy proxy on {host}:{port}")
        else:
            print(f"proxy healthy on {host}:{port}")
        return 0

    # Port open but unhealthy (old proxy without /_gpf/health) — still usable for work
    if port_open(host, port) and not health_ok(host, port):
        # Try a known blocked path — if 403 from our filter, OK
        try:
            urllib.request.urlopen(f"http://{host}:{port}/v1/storage", timeout=2)
        except urllib.error.HTTPError as e:
            if e.code == 403:
                print(f"proxy running on {host}:{port} (legacy health, storage=403)")
                return 0
        except Exception:
            pass
        if verbose:
            print("Port open but health unclear — not restarting (avoid kill)", file=sys.stderr)
        print(f"proxy port open on {host}:{port}")
        return 0

    install_dir = _install_dir()
    if not (install_dir / "xai_filter_proxy.py").is_file():
        print(
            "FEHLER: xai_filter_proxy.py fehlt. Zuerst install_all / install.ps1",
            file=sys.stderr,
        )
        return 1

    if verbose:
        print(f"Proxy down — starting from {install_dir}", file=sys.stderr)

    try:
        start_proxy(install_dir, host, port, verbose)
    except Exception as exc:
        print(f"FEHLER beim Start: {exc}", file=sys.stderr)
        return 1

    deadline = time.time() + wait_secs
    while time.time() < deadline:
        if port_open(host, port):
            print(f"proxy started on {host}:{port}")
            return 0
        time.sleep(0.2)

    print(
        f"FEHLER: Proxy startete nicht in {wait_secs}s "
        f"(~/.grok/proxy/logs/ensure-proxy-daemon.log)",
        file=sys.stderr,
    )
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Ensure xAI filter proxy is running")
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--wait-secs", type=float, default=6.0)
    ap.add_argument(
        "--watchdog",
        action="store_true",
        help="Loop: check every --interval-secs and restart if down",
    )
    ap.add_argument("--interval-secs", type=float, default=60.0)
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    if not args.watchdog:
        return ensure_once(args.host, args.port, args.wait_secs, args.verbose)

    # Watchdog loop (for scheduled task / background)
    log_dir = Path.home() / ".grok" / "proxy" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    wlog = log_dir / "watchdog.log"
    if args.verbose:
        print(f"Watchdog every {args.interval_secs}s", file=sys.stderr)
    while True:
        code = ensure_once(args.host, args.port, args.wait_secs, args.verbose)
        try:
            with open(wlog, "a", encoding="utf-8") as f:
                f.write(
                    f"{time.strftime('%Y-%m-%d %H:%M:%S')} ensure_exit={code}\n"
                )
        except OSError:
            pass
        time.sleep(max(5.0, args.interval_secs))


if __name__ == "__main__":
    raise SystemExit(main())
