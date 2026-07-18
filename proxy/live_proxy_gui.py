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

# Translations for German and English
TRANSLATIONS = {
    'de': {
        'title': 'PROXY LIVE STATUS — Grok Privacy Filter',
        'status_ready': 'Bereit',
        'hooks_note': 'Hooks: /hooks-trust ; dann /hooks r',
        'proxy_status': 'PROXY: ???',
        'schutz_status': 'SCHUTZ: ???',
        'always_on_top': 'Immer oben',
        'start': 'Proxy starten',
        'stop': 'Proxy stoppen',
        'defaults': 'Empfohlene Defaults',
        'full_start': 'Voller Start',
        'extended': 'Erweitert',
        'compact': 'Kompakt',
        'log': 'Log:',
        'log_compact': 'Log (kompakt)',
        'menu_file': 'Datei',
        'menu_settings': 'Einstellungen...',
        'menu_autostart': 'Autostart einrichten',
        'menu_close': 'Schließen',
        'menu_view': 'Ansicht',
        'menu_toggle_view': 'Erweitert / Kompakt umschalten',
        'menu_refresh': 'Jetzt aktualisieren',
        'menu_actions': 'Aktionen',
        'menu_recommended_defaults': 'Empfohlene Datenschutz-Defaults',
        'menu_full_protection': 'Mit vollem Schutz starten',
        'menu_help': 'Hilfe',
        'menu_about': 'Über',
        'settings_title': 'Proxy Einstellungen',
        'welcome_title': 'Willkommen beim Grok Privacy Filter',
        'welcome_text': 'Schnellstart:\n\n1. Klicke „Empfohlene Defaults“ oder „Voller Start“\n2. Proxy läuft automatisch mit Schutz\n\nDanach siehst du „SCHUTZ AKTIV ✓“.\nDie GUI bleibt offen – du siehst live, was blockiert wird.\nMenü (Datei/Ansicht) für weitere Optionen.\n\nViel Erfolg & sicheres Arbeiten!',
        'about_title': 'Über Grok Privacy Filter',
        'about_text': 'Grok Privacy Filter GUI\n\nLokaler Default-Deny-Proxy mit Live-Status.\nVoll transparent und editierbar.\n\nSiehe docs/ANLEITUNG.md und docs/GRENZEN.md',
        'lang_de': 'Deutsch',
        'lang_en': 'English',
        'status_proxy_started': 'Proxy gestartet',
        'status_proxy_stopping': 'Proxy wird gestoppt...',
        'status_proxy_starting': 'Proxy wird gestartet...',
        'status_healthy': 'Proxy healthy',
        'status_defaults_applied': 'Empfohlene Defaults übernommen',
        'status_policy_saved': 'Policy gespeichert',
        'status_full_start': 'Voller Start abgeschlossen',
        'status_blocked': 'Blockiert: Datei | Code/WS | Uploads | Telemetrie | Feedback | Bundles | Sync',
        'proxy_running': 'LAEUFT ✓ (Port {port}, PID {pid})',
        'proxy_stopped': 'GESTOPPT ✗ (Port {port})',
        'protection_active': 'AKTIV ✓',
        'protection_inactive': 'NICHT AKTIV ⚠',
        'protection_error': 'FEHLER',
        'protection_incomplete': 'Schutz nicht vollständig – siehe Einstellungen',
        'theft_prevention': 'DATENKLAU VERHINDERN',
        'data_theft_protection_active': 'Datenklau-Schutz aktiv (blockiert Exfiltration komplett)',
        'blocks_then': 'Blockiert dann: Dateizugriff • Code/Workspace • Uploads • Telemetrie • Feedback • Bundles • Sync',
        'prefixes_below': 'Unten die genauen Prefixe (nur bei Bedarf):',
        'allowed_prefixes': 'Erlaubte Prefixes (allow_prefixes)',
        'denied_prefixes': 'Verbotene Prefixes (deny_prefixes) - Default-Deny',
        'further_settings': 'Weitere Einstellungen',
        'hint_restart': 'Hinweis: Änderungen erfordern meist Proxy-Neustart.',
        'save': 'Speichern',
        'cancel': 'Abbrechen',
        'add': 'Hinzufügen',
        'remove': 'Entfernen',
        'saved_title': 'Gespeichert',
        'saved_text': 'Policy gespeichert.\nProxy neu starten für Übernahme der Änderungen.',
        'verify_hooks': 'Hooks prüfen',
        'hooks_ok': 'Hooks installiert ✓ (in Grok: /hooks-trust ; dann /hooks r)',
        'hooks_missing': 'Hooks fehlen – Install erneut ausführen',
        'hooks_found_msg': 'Hook-Dateien gefunden.\n\nIn Grok: /hooks-trust ausführen\nDann /hooks und \'r\' zum Reload. Prüfen dass block-xai-upload aufgelistet und aktiviert ist.',
        'hooks_missing_msg': 'Hook-Dateien nicht in ~/.grok/hooks/ gefunden.\nBitte install_easy erneut ausführen.',
    },
    'en': {
        'title': 'PROXY LIVE STATUS — Grok Privacy Filter',
        'status_ready': 'Ready',
        'hooks_note': 'Hooks: /hooks-trust ; then /hooks r',
        'proxy_status': 'PROXY: ???',
        'schutz_status': 'PROTECTION: ???',
        'always_on_top': 'Always on top',
        'start': 'Start Proxy',
        'stop': 'Stop Proxy',
        'defaults': 'Recommended Defaults',
        'full_start': 'Full Start',
        'extended': 'Extended',
        'compact': 'Compact',
        'log': 'Log:',
        'log_compact': 'Log (compact)',
        'menu_file': 'File',
        'menu_settings': 'Settings...',
        'menu_autostart': 'Setup autostart',
        'menu_close': 'Close',
        'menu_view': 'View',
        'menu_toggle_view': 'Toggle Extended / Compact',
        'menu_refresh': 'Refresh now',
        'menu_actions': 'Actions',
        'menu_recommended_defaults': 'Recommended Privacy Defaults',
        'menu_full_protection': 'Start with Full Protection',
        'menu_help': 'Help',
        'menu_about': 'About',
        'settings_title': 'Proxy Settings',
        'welcome_title': 'Welcome to Grok Privacy Filter',
        'welcome_text': 'Quick start:\n\n1. Click "Recommended Defaults" or "Full Start"\n2. Proxy starts automatically with protection\n\nYou will then see "PROTECTION ACTIVE ✓".\nThe GUI stays open – you see live what is blocked.\nMenu (File/View) for more options.\n\nGood luck & secure working!',
        'about_title': 'About Grok Privacy Filter',
        'about_text': 'Grok Privacy Filter GUI\n\nLocal Default-Deny-Proxy with live status.\nFully transparent and editable.\n\nSee docs/ANLEITUNG.md and docs/GRENZEN.md',
        'lang_de': 'Deutsch',
        'lang_en': 'English',
        'status_proxy_started': 'Proxy started',
        'status_proxy_stopping': 'Stopping proxy...',
        'status_proxy_starting': 'Starting proxy...',
        'status_healthy': 'Proxy healthy',
        'status_defaults_applied': 'Recommended defaults applied',
        'status_policy_saved': 'Policy saved',
        'status_full_start': 'Full start completed',
        'status_blocked': 'Blocks: file | code/ws | uploads | telemetry | feedback | bundles | sync',
        'proxy_running': 'RUNNING ✓ (Port {port}, PID {pid})',
        'proxy_stopped': 'STOPPED ✗ (Port {port})',
        'protection_active': 'ACTIVE ✓',
        'protection_inactive': 'NOT ACTIVE ⚠',
        'protection_error': 'ERROR',
        'protection_incomplete': 'Protection incomplete – see Settings',
        'theft_prevention': 'DATA THEFT PREVENTION',
        'data_theft_protection_active': 'Data theft protection active (blocks exfiltration completely)',
        'blocks_then': 'Blocks then: file access • code/workspace • uploads • telemetry • feedback • bundles • sync',
        'prefixes_below': 'Exact prefixes below (only if needed):',
        'allowed_prefixes': 'Allowed Prefixes (allow_prefixes)',
        'denied_prefixes': 'Denied Prefixes (deny_prefixes) - Default-Deny',
        'further_settings': 'Further Settings',
        'hint_restart': 'Note: Changes usually require proxy restart.',
        'save': 'Save',
        'cancel': 'Cancel',
        'add': 'Add',
        'remove': 'Remove',
        'saved_title': 'Saved',
        'saved_text': 'Policy saved.\nRestart proxy to apply changes.',
        'verify_hooks': 'Verify Hooks',
        'hooks_ok': 'Hooks installed ✓ (run /hooks-trust in Grok; then /hooks r)',
        'hooks_missing': 'Hooks missing – re-run install',
        'hooks_found_msg': 'Hook files found.\n\nIn Grok run: /hooks-trust\nThen /hooks and press \'r\' to reload. Check that block-xai-upload is listed and enabled.',
        'hooks_missing_msg': 'Hook files not found in ~/.grok/hooks/.\nPlease re-run install_easy.',
    }
}


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
        self.root.geometry("720x300")
        self.root.minsize(600, 240)
        self.root.resizable(True, True)

        self.lang = 'de'  # default German, switchable via menu
        self.menubar = None

        self.root.title(self._tr('title'))
        
        # Dynamic locations (works after install and from source tree)
        self.proxy_dir = get_proxy_dir()
        self.policy_path = get_policy_path()
        self.proxy_log = get_proxy_log_path()
        self.pidfile = get_pidfile_path()
        
        self.current_pid = "?"
        self.protection_active = False
        
        # Immer oben (kann man togglen) - default aus, damit Dialoge nicht verdeckt werden
        self.always_on_top = tk.BooleanVar(value=False)
        self.root.attributes("-topmost", False)

        # Menubar (reduziert die Anzahl dauerhaft sichtbarer Buttons)
        self._create_menubar()

        # Main container - cleaner, less "Matrix" dark theme
        main = tk.Frame(root, bg="#f0f0f0")
        main.pack(fill="both", expand=True, padx=4, pady=2)

        # Statusbar - make it visible and not dark
        status_frame = tk.Frame(main, bg="#e0e0e0", height=20)
        status_frame.pack(fill="x", side="bottom", padx=3, pady=(0,1))
        status_frame.pack_propagate(False)
        self.status_bar = tk.Label(
            status_frame, 
            text=self._tr('status_ready'), 
            anchor="w", 
            font=("TkDefaultFont", 8), 
            fg="#222222", 
            bg="#e8e8e8"
        )
        self.status_bar.pack(fill="x", padx=4)

        # Header - light, clean, professional
        header = tk.Frame(main, bg="#e8e8e8")
        header.pack(fill="x", padx=3, pady=2)
        
        left = tk.Frame(header, bg="#e8e8e8")
        left.pack(side="left")
        
        self.status_label = tk.Label(
            left, 
            text=self._tr('proxy_status'), 
            font=("TkDefaultFont", 9, "bold"),
            fg="#222222",
            bg="#e8e8e8"
        )
        self.status_label.pack(side="left", padx=(5, 10))
        
        self.protection_label = tk.Label(
            left, 
            text=self._tr('schutz_status'), 
            font=("TkDefaultFont", 9, "bold"),
            fg="#222222",
            bg="#e8e8e8"
        )
        self.protection_label.pack(side="left")
        
        right = tk.Frame(header, bg="#e8e8e8")
        right.pack(side="right")
        
        self.time_label = tk.Label(
            right, 
            text="", 
            font=("TkDefaultFont", 8),
            fg="#555555",
            bg="#e8e8e8"
        )
        self.time_label.pack(side="right", padx=5)
        
        # Checkbox für immer oben
        self.top_cb = tk.Checkbutton(
            right, 
            text=self._tr('always_on_top'), 
            variable=self.always_on_top,
            command=self.toggle_topmost,
            font=("TkDefaultFont", 8)
        )
        self.top_cb.pack(side="right", padx=5)

        # Buttons - pack BOTTOM frames FIRST (before expanding log) so they don't disappear
        # Use flat modern style, no dated 2000s borders
        btn_frame = tk.Frame(main, relief="flat", bd=0)
        btn_frame.pack(fill="x", side="bottom", padx=3, pady=2)
        
        # Nur direkte Steuer-Buttons in der Leiste.
        # Alles andere (inkl. Einstellungen, Autostart, Aktualisieren) ist im Menü.
        # Reihenfolge: 1. Proxy starten, 2. Proxy stoppen, 3. Empfohlene Defaults, 4. Voller Start, 5. Erweitert
        self.start_btn = tk.Button(btn_frame, text=self._tr('start'), command=self.start_proxy, width=12)
        self.start_btn.pack(side="left", padx=3, pady=1)
        
        self.stop_btn = tk.Button(btn_frame, text=self._tr('stop'), command=self.stop_proxy, width=12)
        self.stop_btn.pack(side="left", padx=3, pady=1)
        
        self.defaults_btn = tk.Button(
            btn_frame,
            text=self._tr('defaults'),
            command=self.apply_recommended_defaults,
            bg="#004400",
            fg="#aaffaa",
            activebackground="#006600",
            width=16
        )
        self.defaults_btn.pack(side="left", padx=3, pady=1)
        
        self.full_start_btn = tk.Button(btn_frame, text=self._tr('full_start'), command=self.start_everything,
                  bg="#002244", fg="#aaddff", width=12)
        self.full_start_btn.pack(side="left", padx=3, pady=1)
        
        self.view_btn = tk.Button(btn_frame, text=self._tr('compact'), command=self.toggle_view, width=9)
        self.view_btn.pack(side="left", padx=3, pady=1)
        
        self._update_button_states()

        # Log Anzeige - keep some contrast for readability of colored log lines, but not full Matrix
        log_frame = tk.Frame(main, bg="#ffffff")
        log_frame.pack(fill="both", expand=True, padx=3, pady=3)
        
        self.log_label = tk.Label(log_frame, text=self._tr('log'), fg="#333", font=("TkDefaultFont", 8))
        self.log_label.pack(anchor="w")
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=22, 
            font=("TkDefaultFont", 9),
            bg="#f8f8f8",
            fg="#000000",
            insertbackground="#000"
        )
        self.log_text.pack(fill="both", expand=True)
        
        # Start auto refresh
        self.running = True
        self.protection_active = False
        self.compact = True
        self.thread = threading.Thread(target=self.auto_refresh, daemon=True)
        self.thread.start()
        
        # Erster Update
        self.update_now()
        self._update_install_status()
        # Silent check on startup (only status bar, no popup dialog)
        self.verify_hooks(show_dialog=False)

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
                        self._tr('welcome_title'),
                        self._tr('welcome_text')
                    )
                # Flag setzen, damit es nicht wieder kommt
                flag.parent.mkdir(parents=True, exist_ok=True)
                flag.write_text("1", encoding="utf-8")
        except Exception:
            pass  # nie den Start blockieren
    
    def _tr(self, key):
        """Get translated string for current language."""
        return TRANSLATIONS.get(self.lang, TRANSLATIONS['de']).get(key, key)

    def set_language(self, lang):
        """Switch language and refresh all UI texts."""
        if lang not in ('de', 'en'):
            lang = 'de'
        self.lang = lang
        self.refresh_language()

    def refresh_language(self):
        """Update all visible texts to current language."""
        # Main window
        self.root.title(self._tr('title'))

        # Header
        if hasattr(self, 'status_label'):
            self.status_label.config(text=self._tr('proxy_status'))
        if hasattr(self, 'protection_label'):
            self.protection_label.config(text=self._tr('schutz_status'))
        if hasattr(self, 'top_cb'):
            self.top_cb.config(text=self._tr('always_on_top'))

        # Buttons
        if hasattr(self, 'start_btn'):
            self.start_btn.config(text=self._tr('start'))
        if hasattr(self, 'stop_btn'):
            self.stop_btn.config(text=self._tr('stop'))
        if hasattr(self, 'defaults_btn'):
            self.defaults_btn.config(text=self._tr('defaults'))
        if hasattr(self, 'full_start_btn'):
            self.full_start_btn.config(text=self._tr('full_start'))
        if hasattr(self, 'view_btn'):
            self.view_btn.config(text=self._tr('extended'))

        # Log
        if hasattr(self, 'log_label'):
            self.log_label.config(text=self._tr('log'))

        # Status bar
        if hasattr(self, 'status_bar'):
            current = self.status_bar.cget('text')
            if current.startswith(self._tr('status_ready')):
                self.status_bar.config(text= self._tr('status_ready') + " | " + self._tr('hooks_note') )

        # Recreate menubar with new labels
        if self.menubar:
            self.menubar.destroy()
        self._create_menubar()

        # Update dynamic texts
        self.update_now()
        self._update_install_status()  # re-apply install status + hooks note after lang switch

    def toggle_topmost(self):
        self.root.attributes("-topmost", self.always_on_top.get())

    def set_status_bar(self, text: str, fg: str = "#888888"):
        """Zeigt Info in der unteren Statusbar (nicht-modal, platzsparend)."""
        if hasattr(self, 'status_bar'):
            self.status_bar.config(text=text, fg=fg)

    def _update_button_states(self):
        """Enable/disable Start/Stop buttons based on whether proxy is running. Immediate feedback."""
        try:
            is_running = bool(
                self.current_pid and 
                str(self.current_pid).isdigit() and 
                self.current_pid != "?"
            )
            if is_running:
                self.start_btn.config(state="disabled")
                self.stop_btn.config(state="normal")
            else:
                self.start_btn.config(state="normal")
                self.stop_btn.config(state="disabled")
        except Exception:
            pass  # buttons may not exist yet during init

    def _show_about(self):
        messagebox.showinfo(
            self._tr('about_title'),
            self._tr('about_text')
        )

    def verify_hooks(self, show_dialog=True):
        """Check if the block-xai-upload hook files are installed in ~/.grok/hooks/."""
        hooks_dir = get_grok_home() / "hooks"
        hook_json = hooks_dir / "block-xai-upload.json"
        hook_py = hooks_dir / "block-xai-upload.py"
        health_py = hooks_dir / "proxy_health_session.py"

        if hook_json.exists() and hook_py.exists() and health_py.exists():
            self.set_status_bar(self._tr('hooks_ok'), fg="#006600")
            if show_dialog:
                messagebox.showinfo(
                    self._tr('verify_hooks'),
                    self._tr('hooks_found_msg')
                )
        else:
            self.set_status_bar(self._tr('hooks_missing'), fg="#aa0000")
            if show_dialog:
                messagebox.showwarning(
                    self._tr('verify_hooks'),
                    self._tr('hooks_missing_msg')
                )

    def _create_menubar(self):
        """Creates the menubar (with language switch)."""
        menubar = tk.Menu(self.root)

        # File
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label=self._tr('menu_settings'), command=self.open_settings)
        file_menu.add_command(label=self._tr('menu_autostart'), command=self.setup_autostart)
        file_menu.add_separator()
        file_menu.add_command(label=self._tr('menu_close'), command=self.root.destroy)
        menubar.add_cascade(label=self._tr('menu_file'), menu=file_menu)

        # View
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label=self._tr('menu_toggle_view'), command=self.toggle_view)
        view_menu.add_command(label=self._tr('menu_refresh'), command=self.update_now)
        menubar.add_cascade(label=self._tr('menu_view'), menu=view_menu)

        # Language
        lang_menu = tk.Menu(menubar, tearoff=0)
        lang_menu.add_command(label=self._tr('lang_de'), command=lambda: self.set_language('de'))
        lang_menu.add_command(label=self._tr('lang_en'), command=lambda: self.set_language('en'))
        menubar.add_cascade(label="Language" if self.lang == 'en' else "Sprache", menu=lang_menu)

        # Actions
        action_menu = tk.Menu(menubar, tearoff=0)
        action_menu.add_command(label=self._tr('start'), command=self.start_proxy)
        action_menu.add_command(label=self._tr('stop'), command=self.stop_proxy)
        action_menu.add_separator()
        action_menu.add_command(label=self._tr('menu_recommended_defaults'), command=self.apply_recommended_defaults)
        action_menu.add_command(label=self._tr('menu_full_protection'), command=self.start_everything)
        action_menu.add_separator()
        action_menu.add_command(label=self._tr('verify_hooks'), command=self.verify_hooks)
        menubar.add_cascade(label=self._tr('menu_actions'), menu=action_menu)

        # Help
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label=self._tr('menu_about'), command=self._show_about)
        menubar.add_cascade(label=self._tr('menu_help'), menu=help_menu)

        self.root.config(menu=menubar)
        self.menubar = menubar  # keep ref for language refresh if needed

    def toggle_view(self):
        self.compact = not self.compact
        if self.compact:
            self.log_label.config(text=self._tr('log_compact'))
            self.log_text.config(height=5)
            self.view_btn.config(text=self._tr('compact'))
            self.root.geometry("720x280")
            self.root.update_idletasks()
        else:
            self.log_label.config(text=self._tr('log'))
            self.log_text.config(height=25)
            self.view_btn.config(text=self._tr('extended'))
            self.root.geometry("720x450")
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
        """Zeigt Installations-Status in der Statusbar (platzsparend)."""
        issues = self._check_installation()
        note = " | " + self._tr('hooks_note')
        if not issues:
            self.set_status_bar(f"✓ Install OK | {self.proxy_dir}{note}", fg="#006600")
        else:
            txt = "⚠ " + " • ".join(issues) + note
            self.set_status_bar(txt, fg="#aa0000")

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
                    text=self._tr('proxy_status').split(':')[0] + ": " + self._tr('proxy_running').format(port=PORT, pid=pid), 
                    fg="#006600"
                )
                self.set_status_bar(self._tr('status_healthy'), fg="#006600")
                self._update_button_states()
            else:
                self.current_pid = "?"
                self.status_label.config(
                    text=self._tr('proxy_status').split(':')[0] + ": " + self._tr('proxy_stopped').format(port=PORT), 
                    fg="#aa0000"
                )
                self._update_button_states()

            # Datenklau-Schutz Status aktualisieren (einfach & offensichtlich)
            missing = self.check_data_theft_protection()
            if self.protection_active:
                self.protection_label.config(
                    text=self._tr('schutz_status').split(':')[0] + " " + self._tr('protection_active'), 
                    fg="#006600"
                )
                self.set_status_bar(self._tr('status_blocked'), fg="#006600")
            else:
                self.protection_label.config(
                    text=self._tr('schutz_status').split(':')[0] + " " + self._tr('protection_inactive'), 
                    fg="#aa0000"
                )
                self.set_status_bar(self._tr('protection_incomplete'), fg="#aa0000")
        except Exception as e:
            self.status_label.config(text=f"ERROR: {e}" if self.lang == 'en' else f"FEHLER: {e}", fg="#aa0000")
            self.protection_label.config(text=self._tr('schutz_status').split(':')[0] + " " + self._tr('protection_error'), fg="#aa0000")
            self.set_status_bar(f"Error: {e}" if self.lang == 'en' else f"Fehler: {e}", fg="#aa0000")
        
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
                
                self.log_text.tag_config("allow", foreground="#006600")
                self.log_text.tag_config("block", foreground="#aa0000")
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
                messagebox.showwarning("Policy" if self.lang == 'en' else "Policy", f"Could not create policy: {e}" if self.lang == 'en' else f"Konnte Policy nicht anlegen: {e}")

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
                messagebox.showwarning("Data theft protection" if self.lang == 'en' else "Datenklau-Schutz", f"Auto activation partially failed: {e}" if self.lang == 'en' else f"Auto-Aktivierung teilweise fehlgeschlagen: {e}")

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
            self.current_pid = str(proc.pid)
            self.set_status_bar(self._tr('status_proxy_starting'), fg="#006600")
            self._update_button_states()
            self.update_now()  # immediate feedback
            self.root.after(1200, self.update_now)
            self.root.after(1500, lambda: self.verify_hooks(show_dialog=False))  # silent re-check after start
        except Exception as e:
            self.status_label.config(text=f"START ERROR: {e}" if self.lang == 'en' else f"START FEHLER: {e}", fg="#aa0000")
            messagebox.showerror(
                "Start failed" if self.lang == 'en' else "Start fehlgeschlagen",
                f"Could not start proxy.\n\nCommand: {' '.join(py_cmd + [str(proxy_script)])}\n\n"
                f"Error: {e}\n\nTip: Make sure Python 3.10+ is available ('py -3' or 'python3')."
                if self.lang == 'en' else
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

            self.set_status_bar(self._tr('status_defaults_applied'), fg="#006600")
            self.update_now()
        except Exception as e:
            messagebox.showerror("Error applying defaults" if self.lang == 'en' else "Fehler beim Übernehmen der Defaults", str(e))

    def start_everything(self):
        """Phase 4: Proxy + GUI zusammen / Vollstart mit Schutz."""
        self.apply_recommended_defaults()
        if not health_ok("127.0.0.1", PORT):
            self.start_proxy()
        self.update_now()
        messagebox.showinfo("Full start" if self.lang == 'en' else "Vollstart", "Proxy + recommended full protection settings are active." if self.lang == 'en' else "Proxy + die empfohlenen vollen Schutz-Einstellungen sind aktiv.")

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
                    messagebox.showinfo("Autostart" if self.lang == 'en' else "Autostart", "Autostart setup started.\nProxy should start automatically on login." if self.lang == 'en' else "Autostart-Installation wurde gestartet.\nProxy sollte beim Login automatisch laufen.")
                else:
                    messagebox.showinfo("Autostart" if self.lang == 'en' else "Autostart", "Please run manually:\npowershell -ExecutionPolicy Bypass -File scripts\\install_autostart.ps1" if self.lang == 'en' else "Bitte manuell ausführen:\npowershell -ExecutionPolicy Bypass -File scripts\\install_autostart.ps1")
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
            messagebox.showerror("Autostart error" if self.lang == 'en' else "Autostart Fehler", str(e))

    def stop_proxy(self):
        pid = self.current_pid or self._read_pidfile()
        self.set_status_bar(self._tr('status_proxy_stopping'), fg="#aa0000")
        self.current_pid = "?"
        self._update_button_states()
        self.update_now()  # immediate feedback

        if pid and pid.isdigit():
            ok = self._kill_by_pid(pid)
            if ok:
                self._clear_pidfile()
            self.root.after(1000, self.update_now)
            self.root.after(2000, self.update_now)
        else:
            # Last resort: try to stop anything listening on the port (Unix friendly)
            try:
                if os.name != "nt":
                    subprocess.call(["pkill", "-f", "xai_filter_proxy"], stderr=subprocess.DEVNULL)
                self.root.after(1500, self.update_now)
            except Exception as e:
                self.status_label.config(text=f"STOP ERROR: {e}" if self.lang == 'en' else f"STOP FEHLER: {e}", fg="#aa0000")

    def open_settings(self):
        """Öffnet ein Einstellungsfenster für die Proxy-Policy.
        Fokus: Einfache Kontrolle gegen Datenklau (Exfiltration).
        """
        # Temporär topmost deaktivieren, damit Einstellungen-Dialog nicht verdeckt wird
        self._was_top = self.root.attributes("-topmost")
        self.root.attributes("-topmost", False)

        settings_win = tk.Toplevel(self.root)
        settings_win.title(self._tr('settings_title'))
        settings_win.geometry("580x480")
        settings_win.minsize(520, 420)
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
        theft_frame = tk.LabelFrame(settings_win, text=self._tr('theft_prevention'), padx=10, pady=6, fg="#cc0000", font=("Consolas", 11, "bold"))
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
                       text=self._tr('data_theft_protection_active'),
                       variable=self.datenklau_var, command=on_datenklau_toggle,
                       font=("Consolas", 11, "bold"), fg="#990000").pack(anchor="w", pady=2)

        tk.Label(theft_frame, 
                 text=self._tr('blocks_then'),
                 fg="#333", font=("Consolas", 8), wraplength=500).pack(anchor="w", pady=(2,4))

        tk.Label(theft_frame, text=self._tr('prefixes_below'), fg="#666", font=("Consolas", 9)).pack(anchor="w")

        # --- Allow Prefixes ---
        allow_frame = tk.LabelFrame(settings_win, text=self._tr('allowed_prefixes'), padx=8, pady=4)
        allow_frame.pack(fill="x", padx=10, pady=6)

        self.allow_list = tk.Listbox(allow_frame, height=4)
        self.allow_list.pack(side="left", fill="both", expand=True)
        for p in policy.get("allow_prefixes", []):
            self.allow_list.insert("end", p)

        allow_btns = tk.Frame(allow_frame)
        allow_btns.pack(side="right", padx=4)
        self.allow_entry = tk.Entry(allow_btns, width=30)
        self.allow_entry.pack(pady=2)
        tk.Button(allow_btns, text=self._tr('add'), command=lambda: self._add_to_list(self.allow_list, self.allow_entry)).pack(fill="x")
        tk.Button(allow_btns, text=self._tr('remove'), command=lambda: self._remove_from_list(self.allow_list)).pack(fill="x")

        # --- Deny Prefixes ---
        deny_frame = tk.LabelFrame(settings_win, text=self._tr('denied_prefixes'), padx=8, pady=4)
        deny_frame.pack(fill="x", padx=10, pady=6)

        self.deny_list = tk.Listbox(deny_frame, height=5)
        self.deny_list.pack(side="left", fill="both", expand=True)
        for p in policy.get("deny_prefixes", []):
            self.deny_list.insert("end", p)

        deny_btns = tk.Frame(deny_frame)
        deny_btns.pack(side="right", padx=4)
        self.deny_entry = tk.Entry(deny_btns, width=30)
        self.deny_entry.pack(pady=2)
        tk.Button(deny_btns, text=self._tr('add'), command=lambda: self._add_to_list(self.deny_list, self.deny_entry)).pack(fill="x")
        tk.Button(deny_btns, text=self._tr('remove'), command=lambda: self._remove_from_list(self.deny_list)).pack(fill="x")

        # --- Weitere Einstellungen ---
        other_frame = tk.LabelFrame(settings_win, text=self._tr('further_settings'), padx=8, pady=4)
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
        tk.Label(settings_win, text=self._tr('hint_restart'), fg="#666", font=("Consolas", 8)).pack(pady=4)

        # Buttons unten
        btns = tk.Frame(settings_win)
        btns.pack(fill="x", padx=10, pady=8)
        tk.Button(btns, text=self._tr('save'), command=lambda: self._save_policy(settings_win)).pack(side="left", padx=5)
        tk.Button(btns, text=self._tr('cancel'), command=settings_win.destroy).pack(side="right", padx=5)

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

            self.set_status_bar(self._tr('status_policy_saved'), fg="#006600")
            messagebox.showinfo(self._tr('saved_title'), self._tr('saved_text'))
            self.root.attributes("-topmost", self._was_top)  # restore
            win.destroy()

            # Wenn Proxy läuft → automatisch neu starten
            if self.current_pid and self.current_pid.isdigit():
                self.stop_proxy()
                self.root.after(800, self.start_proxy)

            self.update_now()
        except Exception as e:
            messagebox.showerror("Error saving" if self.lang == 'en' else "Fehler beim Speichern", str(e))

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
