#!/usr/bin/env python3
"""
PROXY LIVE STATUS - Immer sichtbares Fenster
Einfaches GUI, das du offen lassen kannst. Zeigt Status + letzte Aktivitaet.

Dynamische Pfade (keine Hardcodes), erste Installationsprüfung,
bessere Fehlermeldungen und grundlegende Cross-Platform-Unterstützung.
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import threading
import time
from datetime import datetime
import os
import json
import sys
import socket
import re
from pathlib import Path
import urllib.request
import urllib.error

PORT = 18743


def get_grok_home() -> Path:
    """Return ~/.grok (respects GROK_HOME env for tests/advanced setups)."""
    return Path(os.environ.get("GROK_HOME", str(Path.home() / ".grok")))


def get_proxy_dir() -> Path:
    """
    Find the directory containing xai_filter_proxy.py + policy.json.

    - If this GUI is executed from a directory that already contains the proxy script
      (dev run: python proxy/live_proxy_gui.py  or after `install` copy), use it.
    - Else fall back to the canonical user location ~/.grok/proxy .
    """
    script_dir = Path(__file__).resolve().parent
    if (script_dir / "xai_filter_proxy.py").is_file():
        return script_dir

    grok_proxy = get_grok_home() / "proxy"
    if (grok_proxy / "xai_filter_proxy.py").is_file() or (grok_proxy / "policy.json").is_file():
        grok_proxy.mkdir(parents=True, exist_ok=True)
        (grok_proxy / "logs").mkdir(parents=True, exist_ok=True)
        return grok_proxy

    # last resort: wherever we are
    return script_dir


def get_policy_path() -> Path:
    """User-writable policy location. Always under ~/.grok for consistency."""
    p = get_grok_home() / "proxy" / "policy.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def get_proxy_log_path() -> Path:
    """Canonical proxy log (the proxy itself prefers ~/.grok/proxy/logs too)."""
    p = get_grok_home() / "proxy" / "logs" / "proxy.log"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def get_pidfile_path() -> Path:
    """Where we remember the PID of proxy started via this GUI."""
    p = get_grok_home() / "proxy" / "gui_proxy.pid"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    """Quick TCP connect check (cross platform)."""
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


def health_ok(host: str, port: int, timeout: float = 1.5) -> bool:
    """Call the proxy's built-in health endpoint (preferred status check)."""
    url = f"http://{host}:{port}/_gpf/health"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            if resp.status != 200:
                return False
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
            return bool(data.get("ok"))
    except Exception:
        return False

# Kritische Prefixe, die für Datenklau (Exfiltration) relevant sind.
# Diese sollten immer in deny_prefixes sein, damit der Proxy Datenklau verhindert.
CRITICAL_DATA_THEFT_DENY = [
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
    "/v1/codebase_upload"
]

class ProxyLiveWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("PROXY LIVE STATUS — Grok Privacy Filter")
        self.root.geometry("720x340")
        self.root.resizable(True, True)
        
        # Dynamic locations (works after install and from source tree)
        self.proxy_dir = get_proxy_dir()
        self.policy_path = get_policy_path()
        self.proxy_log = get_proxy_log_path()
        self.pidfile = get_pidfile_path()
        
        # Immer oben (kann man togglen) - default aus, damit Dialoge nicht verdeckt werden
        self.always_on_top = tk.BooleanVar(value=False)
        self.root.attributes("-topmost", False)
        
        # Header
        header = tk.Frame(root, bg="#1e1e1e")
        header.pack(fill="x", padx=5, pady=5)
        
        self.status_label = tk.Label(
            header, 
            text="PROXY STATUS: ???", 
            font=("Consolas", 14, "bold"),
            fg="yellow",
            bg="#1e1e1e"
        )
        self.status_label.pack(side="left", padx=10)
        
        self.protection_label = tk.Label(
            header, 
            text="DATENKLAU-SCHUTZ: ???", 
            font=("Consolas", 12, "bold"),
            fg="yellow",
            bg="#1e1e1e"
        )
        self.protection_label.pack(side="left", padx=10)
        
        self.time_label = tk.Label(
            header, 
            text="", 
            font=("Consolas", 10),
            fg="#888888",
            bg="#1e1e1e"
        )
        self.time_label.pack(side="right", padx=10)

        # Prominenter Datenklau-Banner im Hauptfenster
        self.datenklau_banner = tk.Label(
            root,
            text="",
            font=("Consolas", 11, "bold"),
            fg="#00ff00",
            bg="#003300"
        )
        self.datenklau_banner.pack(fill="x", padx=5, pady=(0,5))

        # Extra prominenter Schutz-Indikator (Phase 1 + 4 visuelle Verbesserung)
        self.protection_frame = tk.Frame(root, bg="#002200", height=34)
        self.protection_frame.pack(fill="x", padx=5, pady=(0, 4))
        self.protection_frame.pack_propagate(False)
        self.protection_big = tk.Label(
            self.protection_frame,
            text="DATENKLAU-SCHUTZ STATUS",
            font=("Consolas", 13, "bold"),
            fg="#aaffaa",
            bg="#002200"
        )
        self.protection_big.pack(expand=True)

        # Kurzer Willkommens-/Hinweis-Text (Phase 3 + 4)
        self.welcome_label = tk.Label(
            root,
            text="Schnellstart: 'Empfohlene Datenschutz-Defaults' → 'Proxy starten'  |  Alles transparent & editierbar in Einstellungen",
            font=("Consolas", 9, "bold"),
            fg="#aaccff",
            bg="#1e1e1e"
        )
        self.welcome_label.pack(fill="x", padx=5, pady=(0,2))

        # Installations-Status (wird beim Start geprüft – Phase 1)
        self.install_status_label = tk.Label(
            root,
            text="",
            font=("Consolas", 9),
            fg="#ffaa00",
            bg="#222222"
        )
        self.install_status_label.pack(fill="x", padx=5, pady=(0, 3))
        
        # Checkbox für immer oben
        top_cb = tk.Checkbutton(
            header, 
            text="Immer im Vordergrund", 
            variable=self.always_on_top,
            command=self.toggle_topmost,
            fg="white",
            bg="#1e1e1e",
            selectcolor="#333"
        )
        top_cb.pack(side="right", padx=10)
        
        # Log Anzeige
        log_frame = tk.Frame(root)
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.log_label = tk.Label(log_frame, text="Letzte Aktivitaet (Proxy-Log):", fg="#ccc")
        self.log_label.pack(anchor="w")
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=22, 
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#00ff00",
            insertbackground="white"
        )
        self.log_text.pack(fill="both", expand=True)

        # Hinweis für Steuerung
        tk.Label(log_frame, text="Buttons: Start/Stop • Einstellungen • 'Empfohlene Datenschutz-Defaults' (One-Click) • Erweitert", fg="#888").pack(anchor="w")
        
        # Buttons
        btn_frame = tk.Frame(root)
        btn_frame.pack(fill="x", padx=5, pady=5)
        
        tk.Button(btn_frame, text="Proxy starten", command=self.start_proxy).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Proxy stoppen", command=self.stop_proxy).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Einstellungen", command=self.open_settings).pack(side="left", padx=5)

        # One-Click-Defaults (Phase 2)
        btn_defaults = tk.Button(
            btn_frame,
            text="Empfohlene Datenschutz-Defaults",
            command=self.apply_recommended_defaults,
            bg="#004400",
            fg="#aaffaa",
            activebackground="#006600"
        )
        btn_defaults.pack(side="left", padx=5)

        # Phase 4: Vollstart + Autostart
        tk.Button(btn_frame, text="Alles starten (Defaults+Proxy)", command=self.start_everything,
                  bg="#002244", fg="#aaddff").pack(side="left", padx=5)
        tk.Button(btn_frame, text="Autostart einrichten", command=self.setup_autostart,
                  bg="#442200", fg="#ffccaa").pack(side="left", padx=5)

        self.view_btn = tk.Button(btn_frame, text="Erweitert", command=self.toggle_view)
        self.view_btn.pack(side="left", padx=5)
        tk.Button(btn_frame, text="Jetzt aktualisieren", command=self.update_now).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Fenster schließen", command=root.destroy).pack(side="right", padx=5)

        # Initial kompakte Ansicht (kein manuelles Resize nötig)
        self.log_text.config(height=6)
        self.view_btn.config(text="Erweitert")
        self.compact = True
        self.view_mode_label = tk.Label(btn_frame, text="Modus: Kompakt", font=("Consolas", 9), fg="#888")
        self.view_mode_label.pack(side="left", padx=5)
        
        # Start auto refresh
        self.running = True
        self.current_pid = "?"
        self.protection_active = False
        self.compact = True
        self.thread = threading.Thread(target=self.auto_refresh, daemon=True)
        self.thread.start()
        
        # Erster Update
        self.update_now()
        self._update_install_status()

        # Phase 3: Einmaliger Willkommenshinweis beim ersten Start
        self._maybe_show_welcome()
    
    def _maybe_show_welcome(self):
        """Zeigt beim allerersten Start der GUI einen freundlichen Onboarding-Hinweis (einmalig)."""
        flag = get_grok_home() / "proxy" / ".first_run_done"
        try:
            if not flag.exists():
                # Nur zeigen, wenn es wirklich der erste Eindruck ist (keine Policy oder keine Logs)
                if not self.policy_path.is_file() or not self.proxy_log.exists():
                    messagebox.showinfo(
                        "Willkommen beim Grok Privacy Filter",
                        "Schnellstart:\n\n"
                        "1. Klicke „Empfohlene Datenschutz-Defaults“ (oben)\n"
                        "2. Klicke „Proxy starten“\n\n"
                        "Danach siehst du oben grün „DATENKLAU-SCHUTZ AKTIV ✓“.\n\n"
                        "Die GUI bleibt offen – du siehst live, was blockiert wird.\n"
                        "Alles ist editierbar unter „Einstellungen“.\n\n"
                        "Viel Erfolg & sicheres Arbeiten!"
                    )
                # Flag setzen, damit es nicht wieder kommt
                flag.parent.mkdir(parents=True, exist_ok=True)
                flag.write_text("1", encoding="utf-8")
        except Exception:
            pass  # nie den Start blockieren
    
    def toggle_topmost(self):
        self.root.attributes("-topmost", self.always_on_top.get())

    def toggle_view(self):
        self.compact = not self.compact
        if self.compact:
            self.log_label.config(text="Log (kompakt)")
            self.log_text.config(height=5)
            self.datenklau_banner.config(text="Datenklau AKTIV")
            self.view_btn.config(text="Erweitert")
            if hasattr(self, 'view_mode_label'):
                self.view_mode_label.config(text="Modus: Kompakt")
            self.root.geometry("680x300")
            self.root.update_idletasks()
        else:
            self.log_label.config(text="Letzte Aktivitaet (Proxy-Log):")
            self.log_text.config(height=25)
            self.datenklau_banner.config(text="✓ BLOCKIERT: Dateizugriff | Code/Workspace | Uploads | Telemetrie | Feedback | Bundles | Sync")
            if hasattr(self, "protection_big"):
                # in extended view keep big indicator in sync (color may be from last update_now)
                pass
            self.view_btn.config(text="Kompakt")
            if hasattr(self, 'view_mode_label'):
                self.view_mode_label.config(text="Modus: Erweitert")
            self.root.geometry("780x650")
            self.root.update_idletasks()

    def check_data_theft_protection(self):
        """Prüft, ob alle kritischen Datenklau-Pfade in deny_prefixes sind."""
        try:
            if not self.policy_path.is_file():
                self.protection_active = False
                return CRITICAL_DATA_THEFT_DENY[:]
            with open(self.policy_path, "r", encoding="utf-8") as f:
                policy = json.load(f)
            deny = set(policy.get("deny_prefixes", []))
            missing = [p for p in CRITICAL_DATA_THEFT_DENY if p not in deny]
            self.protection_active = len(missing) == 0
            return missing
        except Exception:
            self.protection_active = False
            return CRITICAL_DATA_THEFT_DENY[:]
    
    # ---------- PID helpers (cross platform) ----------
    def _read_pidfile(self) -> str | None:
        try:
            if self.pidfile.is_file():
                pid = self.pidfile.read_text(encoding="utf-8").strip()
                if pid.isdigit():
                    return pid
        except Exception:
            pass
        return None

    def _write_pidfile(self, pid: int) -> None:
        try:
            self.pidfile.write_text(str(pid), encoding="utf-8")
        except Exception:
            pass

    def _clear_pidfile(self) -> None:
        try:
            if self.pidfile.is_file():
                self.pidfile.unlink()
        except Exception:
            pass

    def _pid_alive(self, pid: int) -> bool:
        if pid <= 0:
            return False
        try:
            if os.name == "nt":
                # tasklist is language independent enough for PID match
                res = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                return str(pid) in res.stdout
            else:
                os.kill(pid, 0)  # signal 0 = existence check
                return True
        except Exception:
            return False

    def _get_current_pid(self) -> str | None:
        """Return a plausible PID for the running proxy (pidfile preferred, then discovery)."""
        pid = self._read_pidfile()
        if pid and self._pid_alive(int(pid)):
            return pid

        # Fallback discovery (best effort)
        if os.name == "nt":
            try:
                res = subprocess.run(
                    ["netstat", "-ano"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                for line in res.stdout.splitlines():
                    if f":{PORT}" in line and ("0.0.0.0:0" in line or "::" in line or "LISTENING" in line.upper()):
                        parts = line.strip().split()
                        if parts:
                            cand = parts[-1]
                            if cand.isdigit():
                                return cand
            except Exception:
                pass
        else:
            # Unix: try lsof / ss / netstat (first number that looks like pid)
            for cmd in (["lsof", "-t", "-i", f"tcp:{PORT}", "-sTCP:LISTEN"],
                        ["ss", "-tlnp"],
                        ["netstat", "-tlnp"]):
                try:
                    res = subprocess.run(cmd, capture_output=True, text=True, timeout=1.5)
                    text = res.stdout + res.stderr
                    # crude but effective: look for numbers after pid= or as separate tokens
                    for m in re.finditer(r'(?:pid=)?(\d+)', text):
                        cand = m.group(1)
                        if cand.isdigit() and int(cand) > 1:
                            return cand
                except Exception:
                    continue
        return None

    def _kill_by_pid(self, pid: str) -> bool:
        if not pid or not pid.isdigit():
            return False
        try:
            if os.name == "nt":
                subprocess.call(["taskkill", "/PID", pid, "/F"], creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.call(["kill", pid])
            return True
        except Exception:
            return False

    def _check_installation(self) -> list[str]:
        """Phase 1: Prüft beim Start / bei Bedarf ob Kern-Komponenten vorhanden sind."""
        issues: list[str] = []
        if not (self.proxy_dir / "xai_filter_proxy.py").is_file():
            issues.append("xai_filter_proxy.py fehlt")
        if not self.policy_path.is_file():
            issues.append("policy.json fehlt (wird beim Start automatisch angelegt)")
        # Quick python sanity (non-fatal)
        try:
            _ = self._find_python_cmd()
        except Exception:
            issues.append("Python-Erkennung problematisch")
        return issues

    def _update_install_status(self):
        issues = self._check_installation()
        if not issues:
            self.install_status_label.config(
                text=f"✓ Installations-Check OK  |  Proxy-Verzeichnis: {self.proxy_dir}",
                fg="#88ff88",
                bg="#003300"
            )
        else:
            txt = "⚠ " + " • ".join(issues) + f"   (Dir: {self.proxy_dir})"
            self.install_status_label.config(text=txt, fg="#ffaa00", bg="#331100")

    def update_now(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=now)
        
        # Status via health endpoint (preferred, cross-platform, language independent)
        try:
            is_healthy = health_ok("127.0.0.1", PORT)
            listening = port_open("127.0.0.1", PORT, timeout=0.4)

            pid = self._get_current_pid() or "?"

            if is_healthy or (listening and pid != "?"):
                self.current_pid = pid
                self.status_label.config(
                    text=f"PROXY STATUS: LAEUFT ✓  (Port {PORT}, PID {pid})", 
                    fg="#00ff00"
                )
            else:
                self.current_pid = "?"
                self.status_label.config(
                    text=f"PROXY STATUS: GESTOPPT ✗  (Port {PORT} nicht erreichbar)", 
                    fg="#ff4444"
                )

            # Datenklau-Schutz Status aktualisieren (einfach & offensichtlich)
            missing = self.check_data_theft_protection()
            if self.protection_active:
                self.protection_label.config(
                    text="DATENKLAU-SCHUTZ AKTIV ✓", 
                    fg="#00ff00"
                )
                self.datenklau_banner.config(
                    text="✓ BLOCKIERT: Dateizugriff | Code/Workspace | Uploads | Telemetrie | Feedback | Bundles | Sync",
                    bg="#003300",
                    fg="#00ff00"
                )
                if hasattr(self, "protection_big"):
                    self.protection_big.config(
                        text="✓ DATENKLAU-SCHUTZ AKTIV — ALLES WICHTIGE BLOCKIERT",
                        fg="#88ff88",
                        bg="#002200"
                    )
                    self.protection_frame.config(bg="#002200")
            else:
                self.protection_label.config(
                    text="DATENKLAU-SCHUTZ NICHT AKTIV ⚠", 
                    fg="#ff4444"
                )
                self.datenklau_banner.config(
                    text="⚠ Datenklau-Schutz nicht vollständig – Einstellungen prüfen",
                    bg="#330000",
                    fg="#ff4444"
                )
                if hasattr(self, "protection_big"):
                    self.protection_big.config(
                        text="⚠ DATENKLAU-SCHUTZ INAKTIV — RISIKO VON EXFILTRATION",
                        fg="#ffaaaa",
                        bg="#220000"
                    )
                    self.protection_frame.config(bg="#220000")
        except Exception as e:
            self.status_label.config(text=f"FEHLER: {e}", fg="#ff8800")
            self.protection_label.config(text="DATENKLAU-SCHUTZ: FEHLER", fg="#ff8800")
        
        # Log Eintraege (dynamic path)
        if self.proxy_log.exists():
            try:
                with open(self.proxy_log, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()[-25:]  # mehr Zeilen für bessere Übersicht
                
                self.log_text.config(state="normal")
                self.log_text.delete("1.0", "end")
                
                for line in lines:
                    line = line.rstrip("\n")
                    if "ALLOW" in line:
                        self.log_text.insert("end", line + "\n", "allow")
                    elif "BLOCK" in line or "WARNING" in line:
                        self.log_text.insert("end", line + "\n", "block")
                    else:
                        self.log_text.insert("end", line + "\n")
                
                self.log_text.tag_config("allow", foreground="#00ff00")
                self.log_text.tag_config("block", foreground="#ff4444")
                self.log_text.config(state="disabled")
                self.log_text.see("end")
            except Exception:
                pass

    def _find_python_cmd(self) -> list[str]:
        """Return a working [python, ...] command list. Tries to be robust across installs."""
        candidates: list[list[str]] = []
        exe = sys.executable
        if exe and "python" in exe.lower() and Path(exe).exists():
            candidates.append([exe])

        if os.name == "nt":
            candidates.extend([["py", "-3"], ["python"], ["python3"]])
        else:
            candidates.extend([["python3"], ["python"]])

        for cand in candidates:
            try:
                res = subprocess.run(
                    cand + ["-c", "import sys; print('OK')"],
                    capture_output=True,
                    text=True,
                    timeout=4,
                    creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0),
                )
                if res.returncode == 0 and "OK" in (res.stdout or ""):
                    return cand
            except Exception:
                continue
        # last desperate try
        return ["python3"] if os.name != "nt" else ["py", "-3"]

    def start_proxy(self):
        # 1. Ensure installation basics
        proxy_script = self.proxy_dir / "xai_filter_proxy.py"
        if not proxy_script.is_file():
            messagebox.showerror(
                "Proxy nicht gefunden",
                f"xai_filter_proxy.py fehlt in:\n{self.proxy_dir}\n\n"
                "Bitte install_all.ps1 / install.ps1 ausführen oder aus dem Repo-Root starten."
            )
            return

        # 2. Vor dem Start: Sicherstellen dass voller Datenklau-Schutz aktiv ist
        #    Create policy if completely missing (with safe defaults + full theft blocks)
        if not self.policy_path.is_file():
            try:
                default = {
                    "version": 1,
                    "comment": "Default-deny. Nur was Grok zum Arbeiten braucht. (auto-created by GUI)",
                    "upstream_host": "cli-chat-proxy.grok.com",
                    "upstream_port": 443,
                    "allow_prefixes": [
                        "/v1/chat/completions", "/v1/responses", "/v1/models",
                        "/v1/user", "/v1/privacy/coding-data-retention"
                    ],
                    "allow_get_only_prefixes": ["/v1/settings"],
                    "deny_prefixes": list(CRITICAL_DATA_THEFT_DENY),
                    "block_git_bundle_bodies": True,
                    "block_pack_magic_bodies": True,
                    "max_body_gzip_bytes": 256000,
                    "log_max_bytes": 5242880,
                    "log_backup_count": 5,
                }
                with open(self.policy_path, "w", encoding="utf-8") as f:
                    json.dump(default, f, indent=2, ensure_ascii=False)
            except Exception as e:
                messagebox.showwarning("Policy", f"Konnte Policy nicht anlegen: {e}")

        missing = self.check_data_theft_protection()
        if not self.protection_active:
            # Auto-aktivieren des vollen Schutzes
            try:
                with open(self.policy_path, "r", encoding="utf-8") as f:
                    policy = json.load(f)
                deny = set(policy.get("deny_prefixes", []))
                for p in CRITICAL_DATA_THEFT_DENY:
                    deny.add(p)
                policy["deny_prefixes"] = sorted(list(deny))
                with open(self.policy_path, "w", encoding="utf-8") as f:
                    json.dump(policy, f, indent=2, ensure_ascii=False)
                self.protection_active = True
            except Exception as e:
                messagebox.showwarning("Datenklau-Schutz", f"Auto-Aktivierung teilweise fehlgeschlagen: {e}")

        # 3. Launch
        py_cmd = self._find_python_cmd()
        try:
            if os.name == "nt":
                proc = subprocess.Popen(
                    py_cmd + [str(proxy_script)],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            else:
                proc = subprocess.Popen(
                    py_cmd + [str(proxy_script)],
                    start_new_session=True,
                )
            self._write_pidfile(proc.pid)
            self.root.after(1800, self.update_now)
            # gentle follow-up refresh
            self.root.after(4200, self.update_now)
        except Exception as e:
            self.status_label.config(text=f"START FEHLER: {e}", fg="#ff8800")
            messagebox.showerror(
                "Start fehlgeschlagen",
                f"Konnte Proxy nicht starten.\n\nBefehl: {' '.join(py_cmd + [str(proxy_script)])}\n\n"
                f"Fehler: {e}\n\nTipp: Python 3.10+ prüfen und 'py -3' oder 'python3' verfügbar machen."
            )

    def apply_recommended_defaults(self):
        """Phase 2: One-Click-Button.
        Übernimmt die empfohlenen Datenschutz-Einstellungen:
        - Alle kritischen Exfiltrations-Pfade blocken
        - Sinnvolle Defaults (block git/pack, limits)
        - Policy wird gespeichert + Proxy ggf. neu gestartet
        """
        try:
            # 1. Policy laden oder mit guten Defaults anlegen
            if not self.policy_path.is_file():
                pol = {
                    "version": 1,
                    "comment": "Empfohlene Datenschutz-Defaults via GUI One-Click",
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
                    "deny_prefixes": [],
                    "block_git_bundle_bodies": True,
                    "block_pack_magic_bodies": True,
                    "max_body_gzip_bytes": 256000,
                    "log_max_bytes": 5242880,
                    "log_backup_count": 5,
                }
            else:
                with open(self.policy_path, "r", encoding="utf-8") as f:
                    pol = json.load(f)

            # 2. Kritische deny-Pfade sicherstellen (full data theft protection)
            deny = set(pol.get("deny_prefixes", []))
            for p in CRITICAL_DATA_THEFT_DENY:
                deny.add(p)
            pol["deny_prefixes"] = sorted(list(deny))

            # 3. Weitere empfohlene sichere Defaults
            pol["block_git_bundle_bodies"] = True
            pol["block_pack_magic_bodies"] = True
            if not pol.get("max_body_gzip_bytes"):
                pol["max_body_gzip_bytes"] = 256000
            pol.setdefault("allow_prefixes", [
                "/v1/chat/completions", "/v1/responses", "/v1/models",
                "/v1/user", "/v1/privacy/coding-data-retention"
            ])

            # 4. Speichern
            with open(self.policy_path, "w", encoding="utf-8") as f:
                json.dump(pol, f, indent=2, ensure_ascii=False)

            self.protection_active = True
            self.check_data_theft_protection()  # refresh flag

            messagebox.showinfo(
                "Empfohlene Defaults übernommen",
                "✓ Alle kritischen Datenklau-Pfade blockiert.\n"
                "✓ Gute Defaults für git-bundles, pack, Größenlimits gesetzt.\n\n"
                "Die Änderungen werden beim nächsten Proxy-Start aktiv."
            )

            # 5. Proxy neu starten falls er läuft (Policy übernehmen)
            if health_ok("127.0.0.1", PORT):
                if self.current_pid and str(self.current_pid).isdigit():
                    self.stop_proxy()
                    self.root.after(900, self.start_proxy)
            else:
                # Nicht laufend → direkt starten mit Schutz
                self.start_proxy()

            self.update_now()
        except Exception as e:
            messagebox.showerror("Fehler beim Übernehmen der Defaults", str(e))

    def start_everything(self):
        """Phase 4: Proxy + GUI zusammen / Vollstart mit Schutz."""
        self.apply_recommended_defaults()
        if not health_ok("127.0.0.1", PORT):
            self.start_proxy()
        self.update_now()
        messagebox.showinfo("Vollstart", "Proxy + voller Schutz sind aktiv (oder werden gestartet).")

    def setup_autostart(self):
        """Phase 4: Autostart direkt aus der GUI einrichten (Windows + Unix)."""
        try:
            grok_home = get_grok_home()
            if os.name == "nt":
                script = grok_home / "proxy" / "install_autostart.ps1"  # may not be copied, use from repo? Better call from known location
                # Since GUI is usually run after install, try to call the install script from source or user scripts if present.
                # Practical: run powershell on the original install script if we can find repo, else tell user.
                # Simpler cross-platform friendly approach:
                ps1 = None
                for candidate in [
                    grok_home / "proxy" / "install_autostart.ps1",  # copied by install
                    Path(__file__).resolve().parent.parent / "scripts" / "install_autostart.ps1",
                    Path("scripts/install_autostart.ps1"),
                ]:
                    if candidate.is_file():
                        ps1 = candidate
                        break

                if ps1:
                    subprocess.Popen([
                        "powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps1)
                    ], creationflags=subprocess.CREATE_NO_WINDOW)
                    messagebox.showinfo("Autostart", "Autostart-Installation wurde gestartet.\nProxy sollte beim Login automatisch laufen.")
                else:
                    messagebox.showinfo("Autostart", "Bitte manuell ausführen:\npowershell -ExecutionPolicy Bypass -File scripts\\install_autostart.ps1")
            else:
                # Unix
                sh = grok_home / "proxy" / "install_autostart.sh"
                if not sh.is_file():
                    sh = Path(__file__).resolve().parent.parent / "scripts" / "install_autostart.sh"
                if sh.is_file():
                    subprocess.Popen(["bash", str(sh)], start_new_session=True)
                    messagebox.showinfo("Autostart", "Autostart-Skript ausgeführt.\nSiehe install_autostart.sh für Details (z.B. crontab oder .bashrc).")
                else:
                    messagebox.showinfo("Autostart", "Unter Unix: siehe scripts/install_autostart.sh")
        except Exception as e:
            messagebox.showerror("Autostart Fehler", str(e))

    def stop_proxy(self):
        pid = self.current_pid or self._read_pidfile()
        if pid and pid.isdigit():
            ok = self._kill_by_pid(pid)
            if ok:
                self._clear_pidfile()
            self.root.after(1200, self.update_now)
            self.root.after(2800, self.update_now)
        else:
            # Last resort: try to stop anything listening on the port (Unix friendly)
            try:
                if os.name != "nt":
                    subprocess.call(["pkill", "-f", "xai_filter_proxy"], stderr=subprocess.DEVNULL)
                self.root.after(1500, self.update_now)
            except Exception as e:
                self.status_label.config(text=f"STOP FEHLER: {e}", fg="#ff8800")

    def open_settings(self):
        """Öffnet ein Einstellungsfenster für die Proxy-Policy.
        Fokus: Einfache Kontrolle gegen Datenklau (Exfiltration).
        """
        # Temporär topmost deaktivieren, damit Einstellungen-Dialog nicht verdeckt wird
        self._was_top = self.root.attributes("-topmost")
        self.root.attributes("-topmost", False)

        settings_win = tk.Toplevel(self.root)
        settings_win.title("Proxy Einstellungen")
        settings_win.geometry("650x580")
        settings_win.resizable(True, True)

        # Bring dialog to front
        settings_win.lift()
        settings_win.focus_force()

        def on_settings_close():
            self.root.attributes("-topmost", self._was_top)
            settings_win.destroy()

        settings_win.protocol("WM_DELETE_WINDOW", on_settings_close)

        # Policy laden (dynamic path)
        try:
            with open(self.policy_path, "r", encoding="utf-8") as f:
                policy = json.load(f)
        except Exception:
            policy = {
                "allow_prefixes": [],
                "allow_get_only_prefixes": [],
                "deny_prefixes": [],
                "block_git_bundle_bodies": True,
                "block_pack_magic_bodies": True,
                "max_body_gzip_bytes": 256000,
                "log_max_bytes": 5242880,
                "log_backup_count": 5
            }
        self._last_loaded_policy = policy  # for save to read allow_get_only safely

        # === Datenklau-Schutz – der eine einfache Schalter (keine Presets) ===
        theft_frame = tk.LabelFrame(settings_win, text="DATENKLAU VERHINDERN", padx=10, pady=6, fg="#cc0000", font=("Consolas", 11, "bold"))
        theft_frame.pack(fill="x", padx=10, pady=8)

        self.datenklau_var = tk.BooleanVar(value=self.protection_active)

        def on_datenklau_toggle():
            if self.datenklau_var.get():
                # Sicherstellen, dass alle kritischen Blöcke da sind
                current = list(self.deny_list.get(0, "end"))
                for p in CRITICAL_DATA_THEFT_DENY:
                    if p not in current:
                        current.append(p)
                self.deny_list.delete(0, "end")
                for p in current:
                    self.deny_list.insert("end", p)

        tk.Checkbutton(theft_frame, 
                       text="Datenklau-Schutz aktiv (blockiert Exfiltration komplett)",
                       variable=self.datenklau_var, command=on_datenklau_toggle,
                       font=("Consolas", 11, "bold"), fg="#990000").pack(anchor="w", pady=2)

        tk.Label(theft_frame, 
                 text="Blockiert dann: Dateizugriff • Code/Workspace auslesen • Uploads • Telemetrie • Feedback • Bundles • Sync",
                 fg="#333", font=("Consolas", 9)).pack(anchor="w", pady=(2,4))

        tk.Label(theft_frame, text="Unten die genauen Prefixe (nur bei Bedarf):", fg="#666", font=("Consolas", 9)).pack(anchor="w")

        # --- Allow Prefixes ---
        allow_frame = tk.LabelFrame(settings_win, text="Erlaubte Prefixes (allow_prefixes)", padx=8, pady=4)
        allow_frame.pack(fill="x", padx=10, pady=6)

        self.allow_list = tk.Listbox(allow_frame, height=5)
        self.allow_list.pack(side="left", fill="both", expand=True)
        for p in policy.get("allow_prefixes", []):
            self.allow_list.insert("end", p)

        allow_btns = tk.Frame(allow_frame)
        allow_btns.pack(side="right", padx=4)
        self.allow_entry = tk.Entry(allow_btns, width=30)
        self.allow_entry.pack(pady=2)
        tk.Button(allow_btns, text="Hinzufügen", command=lambda: self._add_to_list(self.allow_list, self.allow_entry)).pack(fill="x")
        tk.Button(allow_btns, text="Entfernen", command=lambda: self._remove_from_list(self.allow_list)).pack(fill="x")

        # --- Deny Prefixes ---
        deny_frame = tk.LabelFrame(settings_win, text="Verbotene Prefixes (deny_prefixes) - Default-Deny", padx=8, pady=4)
        deny_frame.pack(fill="x", padx=10, pady=6)

        self.deny_list = tk.Listbox(deny_frame, height=6)
        self.deny_list.pack(side="left", fill="both", expand=True)
        for p in policy.get("deny_prefixes", []):
            self.deny_list.insert("end", p)

        deny_btns = tk.Frame(deny_frame)
        deny_btns.pack(side="right", padx=4)
        self.deny_entry = tk.Entry(deny_btns, width=30)
        self.deny_entry.pack(pady=2)
        tk.Button(deny_btns, text="Hinzufügen", command=lambda: self._add_to_list(self.deny_list, self.deny_entry)).pack(fill="x")
        tk.Button(deny_btns, text="Entfernen", command=lambda: self._remove_from_list(self.deny_list)).pack(fill="x")

        # --- Weitere Einstellungen ---
        other_frame = tk.LabelFrame(settings_win, text="Weitere Einstellungen", padx=8, pady=4)
        other_frame.pack(fill="x", padx=10, pady=6)

        self.block_git = tk.BooleanVar(value=policy.get("block_git_bundle_bodies", True))
        tk.Checkbutton(other_frame, text="block_git_bundle_bodies", variable=self.block_git).pack(anchor="w")

        self.block_pack = tk.BooleanVar(value=policy.get("block_pack_magic_bodies", True))
        tk.Checkbutton(other_frame, text="block_pack_magic_bodies", variable=self.block_pack).pack(anchor="w")

        tk.Label(other_frame, text="max_body_gzip_bytes:").pack(anchor="w")
        self.max_gzip = tk.Entry(other_frame, width=15)
        self.max_gzip.insert(0, str(policy.get("max_body_gzip_bytes", 256000)))
        self.max_gzip.pack(anchor="w")

        tk.Label(other_frame, text="log_max_bytes:").pack(anchor="w")
        self.log_max = tk.Entry(other_frame, width=15)
        self.log_max.insert(0, str(policy.get("log_max_bytes", 5242880)))
        self.log_max.pack(anchor="w")

        tk.Label(other_frame, text="log_backup_count:").pack(anchor="w")
        self.log_backup = tk.Entry(other_frame, width=8)
        self.log_backup.insert(0, str(policy.get("log_backup_count", 5)))
        self.log_backup.pack(anchor="w")

        # Hinweis
        tk.Label(settings_win, text="Hinweis: Änderungen erfordern in der Regel einen Neustart des Proxys.", fg="#666").pack(pady=6)

        # Buttons unten
        btns = tk.Frame(settings_win)
        btns.pack(fill="x", padx=10, pady=8)
        tk.Button(btns, text="Speichern", command=lambda: self._save_policy(settings_win)).pack(side="left", padx=5)
        tk.Button(btns, text="Abbrechen", command=settings_win.destroy).pack(side="right", padx=5)

    def _add_to_list(self, lst, entry):
        val = entry.get().strip()
        if val:
            lst.insert("end", val)
            entry.delete(0, "end")

    def _remove_from_list(self, lst):
        sel = lst.curselection()
        if sel:
            lst.delete(sel[0])

    def _save_policy(self, win):
        try:
            # Safely capture previous allow_get_only
            prev_get_only = []
            try:
                if hasattr(self, "_last_loaded_policy") and isinstance(self._last_loaded_policy, dict):
                    prev_get_only = list(self._last_loaded_policy.get("allow_get_only_prefixes", []))
            except Exception:
                prev_get_only = []

            new_policy = {
                "version": 1,
                "comment": "Default-deny. Nur was Grok zum Arbeiten braucht. Bei Chat-403: BLOCK-Log pruefen und hier vorsichtig ergaenzen.",
                "upstream_host": "cli-chat-proxy.grok.com",
                "upstream_port": 443,
                "allow_prefixes": list(self.allow_list.get(0, "end")),
                "allow_get_only_prefixes": prev_get_only,
                "deny_prefixes": (lambda d: d + [p for p in CRITICAL_DATA_THEFT_DENY if self.datenklau_var.get() and p not in d])(list(self.deny_list.get(0, "end"))),
                "block_git_bundle_bodies": self.block_git.get(),
                "block_pack_magic_bodies": self.block_pack.get(),
                "max_body_gzip_bytes": int(self.max_gzip.get() or 256000),
                "log_max_bytes": int(self.log_max.get() or 5242880),
                "log_backup_count": int(self.log_backup.get() or 5)
            }

            with open(self.policy_path, "w", encoding="utf-8") as f:
                json.dump(new_policy, f, indent=2, ensure_ascii=False)

            messagebox.showinfo("Gespeichert", "Policy gespeichert.\nProxy neu starten für Übernahme der Änderungen.")
            self.root.attributes("-topmost", self._was_top)  # restore
            win.destroy()

            # Wenn Proxy läuft → automatisch neu starten
            if self.current_pid and self.current_pid.isdigit():
                self.stop_proxy()
                self.root.after(800, self.start_proxy)

            self.update_now()
        except Exception as e:
            messagebox.showerror("Fehler beim Speichern", str(e))

    def auto_refresh(self):
        while self.running:
            try:
                self.root.after(0, self.update_now)
            except:
                pass
            time.sleep(2)
    
    def on_close(self):
        self.running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ProxyLiveWindow(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
