#!/usr/bin/env python3
"""
Lokaler Default-Deny-Proxy vor cli-chat-proxy.grok.com.

Laesst nur erlaubte Pfade durch (Chat/Inference, User, Settings-GET, Privacy).
Blockt Storage/Upload und alles Unbekannte. Streamt SSE chunkweise.

Voraussetzungen: Python 3.10+

Start:
  python proxy/xai_filter_proxy.py
  # oder: scripts/start_proxy.cmd / scripts/start_proxy.sh

Grok:
  GROK_CLI_CHAT_PROXY_BASE_URL=http://127.0.0.1:18743/v1 grok
"""
from __future__ import annotations

import argparse
import http.client
import json
import logging
import ssl
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterable

UPSTREAM_HOST = "cli-chat-proxy.grok.com"
UPSTREAM_PORT = 443
DEFAULT_BIND = "127.0.0.1"
DEFAULT_PORT = 18743

# Logs neben diesem Repo ODER unter ~/.grok/proxy/logs
_PKG_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR_CANDIDATES = (
    _PKG_ROOT / "logs",
    Path.home() / ".grok" / "proxy" / "logs",
)

ALLOW_PREFIXES: tuple[str, ...] = (
    "/v1/chat/completions",
    "/v1/responses",
    "/v1/models",
    "/v1/user",
    "/v1/privacy/coding-data-retention",
)

ALLOW_GET_ONLY: tuple[str, ...] = (
    "/v1/settings",
)

DENY_PREFIXES: tuple[str, ...] = (
    "/v1/storage",
    "/v1/upload",
    "/storage",
    "/v1/codebase",
    "/v1/workspace",
    "/v1/sync",
    "/v1/trace",
    "/v1/telemetry",
    "/v1/feedback",
)

HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}

log = logging.getLogger("xai_filter_proxy")


def _pick_log_dir() -> Path:
    for d in LOG_DIR_CANDIDATES:
        try:
            d.mkdir(parents=True, exist_ok=True)
            return d
        except OSError:
            continue
    d = Path.cwd() / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _setup_logging(verbose: bool) -> Path:
    log_dir = _pick_log_dir()
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    logfile = log_dir / f"proxy-{day}.log"
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(logfile, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )
    log.info("Logfile: %s", logfile)
    return logfile


def _path_allowed(method: str, path: str) -> tuple[bool, str]:
    path_only = path.split("?", 1)[0]
    for d in DENY_PREFIXES:
        if path_only == d or path_only.startswith(d + "/"):
            return False, f"deny-list: {d}"
    for g in ALLOW_GET_ONLY:
        if path_only == g or path_only.startswith(g + "/"):
            if method.upper() == "GET":
                return True, f"get-only allow: {g}"
            return False, f"get-only, method {method} blocked: {g}"
    for a in ALLOW_PREFIXES:
        if path_only == a or path_only.startswith(a + "/"):
            return True, f"allow: {a}"
    return False, "default-deny"


def _filter_headers(headers: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for k, v in headers:
        if k.lower() in HOP_BY_HOP:
            continue
        out.append((k, v))
    return out


class FilterHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    upstream_host = UPSTREAM_HOST
    upstream_port = UPSTREAM_PORT

    def log_message(self, fmt: str, *args) -> None:
        log.info("http: " + fmt, *args)

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return b""
        return self.rfile.read(length)

    def _send_block(self, reason: str, method: str, path: str) -> None:
        body = json.dumps(
            {
                "error": "blocked_by_local_xai_filter_proxy",
                "reason": reason,
                "method": method,
                "path": path,
                "hint": "Only inference/user/privacy allowed. Storage/upload = default-deny.",
            },
            ensure_ascii=False,
        ).encode("utf-8")
        log.warning("BLOCK %s %s (%s)", method, path, reason)
        self.send_response(403)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def _normalize_path(self, raw_path: str) -> str:
        path = raw_path or "/"
        if path.startswith("/v1/"):
            return path
        if path.startswith("/chat/") or path == "/chat/completions":
            return "/v1" + path
        for prefix in (
            "/models",
            "/user",
            "/settings",
            "/privacy",
            "/responses",
            "/storage",
            "/upload",
        ):
            if path == prefix or path.startswith(prefix + "/"):
                return "/v1" + path
        return path

    def _proxy(self, method: str) -> None:
        path = self._normalize_path(self.path or "/")
        ok, reason = _path_allowed(method, path)
        if not ok:
            self._send_block(reason, method, path)
            return

        body = self._read_body() if method in ("POST", "PUT", "PATCH") else b""

        # Heuristik: Git-Pack / Bundle nicht durchlassen
        if body[:4] == b"PACK" or (len(body) > 256_000 and body[:2] == b"\x1f\x8b"):
            self._send_block("binary-pack-or-large-gzip", method, path)
            return
        head = body[:4096].lower()
        if b"git-bundle" in head or b"PACK\x00" in body[:64]:
            self._send_block("git-bundle-signature", method, path)
            return

        headers = _filter_headers(self.headers.items())
        if body:
            headers = [(k, v) for k, v in headers if k.lower() != "content-length"]
            headers.append(("Content-Length", str(len(body))))

        log.info("ALLOW %s %s (%s) bytes=%s", method, path, reason, len(body))

        ctx = ssl.create_default_context()
        conn = http.client.HTTPSConnection(
            self.upstream_host, self.upstream_port, context=ctx, timeout=600
        )
        try:
            conn.putrequest(method, path, skip_host=False, skip_accept_encoding=True)
            conn.putheader("Host", self.upstream_host)
            for k, v in headers:
                conn.putheader(k, v)
            conn.endheaders(body if body else None)

            resp = conn.getresponse()
            self.send_response(resp.status, resp.reason)
            for k, v in resp.getheaders():
                if k.lower() in HOP_BY_HOP or k.lower() == "content-length":
                    continue
                self.send_header(k, v)
            self.send_header("Connection", "close")
            self.end_headers()

            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                self.wfile.write(chunk)
                try:
                    self.wfile.flush()
                except Exception:
                    break
        except Exception as exc:
            log.exception("upstream error: %s", exc)
            try:
                err = json.dumps(
                    {"error": "upstream_failed", "detail": str(exc)}
                ).encode()
                self.send_response(502)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(err)))
                self.end_headers()
                self.wfile.write(err)
            except Exception:
                pass
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def do_GET(self) -> None:  # noqa: N802
        self._proxy("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._proxy("POST")

    def do_PUT(self) -> None:  # noqa: N802
        self._proxy("PUT")

    def do_PATCH(self) -> None:  # noqa: N802
        self._proxy("PATCH")

    def do_DELETE(self) -> None:  # noqa: N802
        self._proxy("DELETE")

    def do_HEAD(self) -> None:  # noqa: N802
        self._proxy("HEAD")


def main() -> int:
    ap = argparse.ArgumentParser(description="xAI filter proxy (default-deny)")
    ap.add_argument("--bind", default=DEFAULT_BIND)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    _setup_logging(args.verbose)
    server = ThreadingHTTPServer((args.bind, args.port), FilterHandler)
    log.info(
        "Listening http://%s:%s → https://%s (default-deny)",
        args.bind,
        args.port,
        UPSTREAM_HOST,
    )
    log.info("Allow: %s", ", ".join(ALLOW_PREFIXES + ALLOW_GET_ONLY))
    log.info("Deny:  %s + default", ", ".join(DENY_PREFIXES))
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        log.info("shutdown")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
