#!/usr/bin/env python3
"""
Grok Build PreToolUse-Hook: blockiert Agent-seitige Uploads zu xAI/Grok-Hosts.

Scope (ehrlich):
  - Blockiert TOOL-Aufrufe des Agents (Shell curl/wget, web_fetch, …)
    die Daten an xAI/Grok/GCS pushen.
  - Blockiert NICHT den internen Netzwerkverkehr der grok.exe
    (Inference über cli-chat-proxy) — dafür proxy/ nutzen.

Installation: siehe docs/ANLEITUNG.md oder scripts/install.*
"""
from __future__ import annotations

import json
import re
import sys
from typing import Any

BLOCK_HOSTS = (
    r"x\.ai",
    r"grok\.com",
    r"cli-chat-proxy\.grok\.com",
    r"code\.grok\.com",
    r"api\.x\.ai",
    r"auth\.x\.ai",
    r"assets\.grok\.com",
    r"accounts\.x\.ai",
    r"storage\.googleapis\.com",
    r"googleapis\.com",
)

UPLOAD_VERBS = (
    r"curl\b",
    r"wget\b",
    r"httpie\b",
    r"\bhttp\b",
    r"invoke-webrequest",
    r"\biwr\b",
    r"invoke-restmethod",
    r"\birm\b",
    r"start-bitstransfer",
    r"bitsadmin",
    r"scp\b",
    r"rsync\b",
    r"sftp\b",
    r"ftp\b",
    r"nc\b",
    r"ncat\b",
    r"netcat\b",
    r"aria2c\b",
    r"fetch\b",
)

PUSH_HINTS = (
    r"-X\s*POST",
    r"-X\s*PUT",
    r"-X\s*PATCH",
    r"-X\s*DELETE",
    r"--data\b",
    r"--data-raw\b",
    r"--data-binary\b",
    r"-d\s",
    r"--upload-file\b",
    r"-T\s",
    r"--form\b",
    r"-F\s",
    r"method\s+post",
    r"method\s+put",
    r"-method\s+post",
    r"-method\s+put",
    r"infiles?",
    r"multipart",
    r"upload",
    r"git\s+push",
    r"git\s+bundle",
)

HOST_RE = re.compile("|".join(BLOCK_HOSTS), re.I)
UPLOAD_RE = re.compile("|".join(UPLOAD_VERBS), re.I)
PUSH_RE = re.compile("|".join(PUSH_HINTS), re.I)

URL_TOOLS = frozenset(
    {
        "web_fetch",
        "WebFetch",
        "open_page",
        "open_page_with_find",
        "browse_page",
        "mcp_web_fetch",
    }
)

SHELL_TOOLS = frozenset(
    {
        "run_terminal_command",
        "Bash",
        "bash",
        "Shell",
        "shell",
    }
)


def _allow() -> None:
    print(json.dumps({"decision": "allow"}))
    sys.exit(0)


def _deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "decision": "deny",
                "reason": (
                    f"[block-xai-upload] {reason} "
                    "(Agent upload to xAI/Grok hosts blocked. "
                    "CLI inference traffic is NOT blocked by this hook.)"
                ),
            }
        )
    )
    sys.exit(0)


def _flatten(obj: Any) -> str:
    if obj is None:
        return ""
    if isinstance(obj, str):
        return obj
    try:
        return json.dumps(obj, ensure_ascii=False)
    except Exception:
        return str(obj)


def _shell_command(tool_input: dict) -> str:
    for key in ("command", "cmd", "script"):
        val = tool_input.get(key)
        if isinstance(val, str):
            return val
    return _flatten(tool_input)


def _url_from_input(tool_input: dict) -> str:
    for key in ("url", "uri", "href", "target", "endpoint"):
        val = tool_input.get(key)
        if isinstance(val, str):
            return val
    return ""


def _blocked_host_hit(text: str) -> str | None:
    m = HOST_RE.search(text or "")
    return m.group(0) if m else None


def check(payload: dict) -> None:
    tool = (payload.get("toolName") or payload.get("tool_name") or "").strip()
    tool_input = payload.get("toolInput") or payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}

    if tool in URL_TOOLS or tool.lower().endswith("web_fetch"):
        url = _url_from_input(tool_input) or _flatten(tool_input)
        hit = _blocked_host_hit(url)
        if hit:
            _deny(f"network tool to blocked host: {hit}")

    if tool in SHELL_TOOLS or tool.lower() in {"bash", "shell"}:
        cmd = _shell_command(tool_input)
        host = _blocked_host_hit(cmd)
        if host:
            if UPLOAD_RE.search(cmd) or PUSH_RE.search(cmd):
                _deny(f"shell upload/push to {host}")
            if re.search(r"(curl|wget|iwr|irm|invoke-webrequest|scp|rsync)", cmd, re.I):
                _deny(f"shell network command to {host}")

    blob = f"{tool} {_flatten(tool_input)}"
    host = _blocked_host_hit(blob)
    if host and UPLOAD_RE.search(blob) and PUSH_RE.search(blob):
        _deny(f"tool payload targets upload to {host}")

    _allow()


def main() -> None:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            _allow()
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            _allow()
        check(payload)
    except Exception:
        _allow()


if __name__ == "__main__":
    main()
