#!/usr/bin/env python3
"""
Lokaler Default-Deny-Proxy vor cli-chat-proxy.grok.com.

- Policy: proxy/policy.json (oder ~/.grok/proxy/policy.json)
- Health: GET /_gpf/health  (lokal, nie Upstream)
- Streamt SSE; blockt Storage/Upload und Unbekanntes
- Log-Rotation

Voraussetzungen: Python 3.10+
"""
from __future__ import annotations

import argparse
import http.client
import json
import logging
import ssl
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterable

DEFAULT_BIND = "127.0.0.1"
DEFAULT_PORT = 18743

_PKG_ROOT = Path(__file__).resolve().parent.parent
_PROXY_DIR = Path(__file__).resolve().parent

DEFAULT_POLICY: dict[str, Any] = {
    "upstream_host": "cli-chat-proxy.grok.com",
    "upstream_port": 443,
    "allow_prefixes": [
        "/v1/chat/completions",
        "/v1/responses",
        "/v1/models",
        "/v1/user",
        "/v1/privacy/coding-data-retention",
    ],
    "allow_get_only_prefixes": ["/v1/settings"],
    "deny_prefixes": [
        "/v1/storage",
        "/v1/upload",
        "/storage",
        "/v1/codebase",
        "/v1/workspace",
        "/v1/sync",
        "/v1/trace",
        "/v1/telemetry",
        "/v1/feedback",
        "/v1/bundle",
        "/v1/codebase_upload",
    ],
    "block_git_bundle_bodies": True,
    "block_pack_magic_bodies": True,
    "max_body_gzip_bytes": 256000,
    "log_max_bytes": 5_242_880,
    "log_backup_count": 5,
}

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
POLICY: dict[str, Any] = dict(DEFAULT_POLICY)


def _policy_paths() -> list[Path]:
    return [
        Path.home() / ".grok" / "proxy" / "policy.json",
        _PROXY_DIR / "policy.json",
        _PKG_ROOT / "proxy" / "policy.json",
    ]


def load_policy(path: Path | None = None) -> dict[str, Any]:
    merged = dict(DEFAULT_POLICY)
    candidates = [path] if path else _policy_paths()
    for p in candidates:
        if p is None or not p.is_file():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                merged.update({k: v for k, v in data.items() if not str(k).startswith("_")})
                merged["_loaded_from"] = str(p)
                return merged
        except Exception as exc:
            print(f"WARN: policy {p}: {exc}", file=sys.stderr)
    merged["_loaded_from"] = "builtin-defaults"
    return merged


def _pick_log_dir() -> Path:
    for d in (
        Path.home() / ".grok" / "proxy" / "logs",
        _PKG_ROOT / "logs",
        Path.cwd() / "logs",
    ):
        try:
            d.mkdir(parents=True, exist_ok=True)
            return d
        except OSError:
            continue
    return Path.cwd()


def _setup_logging(verbose: bool) -> Path:
    log_dir = _pick_log_dir()
    logfile = log_dir / "proxy.log"
    max_bytes = int(POLICY.get("log_max_bytes") or 5_242_880)
    backups = int(POLICY.get("log_backup_count") or 5)
    level = logging.DEBUG if verbose else logging.INFO
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh = RotatingFileHandler(
        logfile, maxBytes=max_bytes, backupCount=backups, encoding="utf-8"
    )
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    root.addHandler(fh)
    root.addHandler(sh)
    log.info("Logfile: %s (rotate max=%s backups=%s)", logfile, max_bytes, backups)
    return logfile


def _match_prefix(path: str, prefixes: Iterable[str]) -> str | None:
    for p in prefixes:
        if path == p or path.startswith(p + "/"):
            return p
    return None


def path_allowed(method: str, path: str) -> tuple[bool, str]:
    path_only = path.split("?", 1)[0]
    deny = POLICY.get("deny_prefixes") or []
    get_only = POLICY.get("allow_get_only_prefixes") or []
    allow = POLICY.get("allow_prefixes") or []

    hit = _match_prefix(path_only, deny)
    if hit:
        return False, f"deny-list:{hit}"

    hit = _match_prefix(path_only, get_only)
    if hit:
        if method.upper() == "GET" or method.upper() == "HEAD":
            return True, f"get-only:{hit}"
        return False, f"get-only-method-blocked:{method}:{hit}"

    hit = _match_prefix(path_only, allow)
    if hit:
        return True, f"allow:{hit}"

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

    def log_message(self, fmt: str, *args) -> None:
        log.info("http: " + fmt, *args)

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return b""
        # Sanity: no multi-GB uploads through us
        if length > 50 * 1024 * 1024:
            return b""  # treated empty; method will still run — better reject
        return self.rfile.read(length)

    def _send_json(self, code: int, obj: dict) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def _send_block(self, reason: str, method: str, path: str) -> None:
        log.warning(
            "BLOCK method=%s path=%s reason=%s | tip=bei-Chat-Bruch-policy.json-pruefen",
            method,
            path,
            reason,
        )
        self._send_json(
            403,
            {
                "error": "blocked_by_local_xai_filter_proxy",
                "reason": reason,
                "method": method,
                "path": path,
                "hint": "default-deny. Work paths: chat/models/user/privacy/settings-GET. See policy.json + logs.",
            },
        )

    def _normalize_path(self, raw_path: str) -> str:
        path = raw_path or "/"
        if path.startswith("/v1/") or path.startswith("/_gpf/"):
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

    def _local_health(self) -> None:
        self._send_json(
            200,
            {
                "ok": True,
                "service": "grok-privacy-filter-proxy",
                "upstream": POLICY.get("upstream_host"),
                "policy": POLICY.get("_loaded_from"),
                "ts": datetime.now(timezone.utc).isoformat(),
            },
        )

    def _body_blocked(self, body: bytes, path: str) -> str | None:
        if not body:
            return None
        # Never apply pack heuristics to pure chat if tiny — still block PACK magic anywhere
        if POLICY.get("block_pack_magic_bodies", True):
            if body[:4] == b"PACK":
                return "pack-magic"
            if b"PACK\x00" in body[:64]:
                return "pack-nul"
        if POLICY.get("block_git_bundle_bodies", True):
            if b"git-bundle" in body[:4096].lower():
                return "git-bundle-string"
        max_gz = int(POLICY.get("max_body_gzip_bytes") or 256000)
        if len(body) > max_gz and body[:2] == b"\x1f\x8b":
            # large gzip only block off chat path
            if not path.startswith("/v1/chat/"):
                return "large-gzip-non-chat"
        if len(body) > 50 * 1024 * 1024:
            return "body-too-large"
        return None

    def _proxy(self, method: str) -> None:
        path = self._normalize_path(self.path or "/")

        # Local control plane — never upstream
        if path.split("?", 1)[0] in ("/_gpf/health", "/_gpf/health/"):
            if method in ("GET", "HEAD"):
                self._local_health()
                return
            self._send_block("health-get-only", method, path)
            return

        ok, reason = path_allowed(method, path)
        if not ok:
            self._send_block(reason, method, path)
            return

        length = int(self.headers.get("Content-Length") or 0)
        if length > 50 * 1024 * 1024:
            self._send_block("content-length-too-large", method, path)
            return

        body = self._read_body() if method in ("POST", "PUT", "PATCH") else b""
        br = self._body_blocked(body, path)
        if br:
            self._send_block(br, method, path)
            return

        headers = _filter_headers(self.headers.items())
        if body:
            headers = [(k, v) for k, v in headers if k.lower() != "content-length"]
            headers.append(("Content-Length", str(len(body))))

        up_host = str(POLICY.get("upstream_host") or "cli-chat-proxy.grok.com")
        up_port = int(POLICY.get("upstream_port") or 443)
        log.info(
            "ALLOW method=%s path=%s reason=%s bytes=%s",
            method,
            path,
            reason,
            len(body),
        )

        ctx = ssl.create_default_context()
        conn = http.client.HTTPSConnection(up_host, up_port, context=ctx, timeout=600)
        try:
            conn.putrequest(method, path, skip_host=False, skip_accept_encoding=True)
            conn.putheader("Host", up_host)
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
                self._send_json(502, {"error": "upstream_failed", "detail": str(exc)})
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
    global POLICY
    ap = argparse.ArgumentParser(description="xAI filter proxy (default-deny)")
    ap.add_argument("--bind", default=DEFAULT_BIND)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--policy", type=Path, default=None, help="Path to policy.json")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    POLICY = load_policy(args.policy)
    _setup_logging(args.verbose)
    log.info("Policy: %s", POLICY.get("_loaded_from"))
    log.info(
        "Listening http://%s:%s -> https://%s (default-deny)",
        args.bind,
        args.port,
        POLICY.get("upstream_host"),
    )
    log.info("Allow: %s", ", ".join(POLICY.get("allow_prefixes") or []))
    log.info("Get-only: %s", ", ".join(POLICY.get("allow_get_only_prefixes") or []))
    log.info("Deny: %s + default", ", ".join(POLICY.get("deny_prefixes") or []))

    server = ThreadingHTTPServer((args.bind, args.port), FilterHandler)
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        log.info("shutdown")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
