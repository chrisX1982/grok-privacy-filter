#!/usr/bin/env python3
"""
PROXY LIVE STATUS - Immer sichtbares Fenster
Einfaches GUI, das du offen lassen kannst. Zeigt Status + letzte Aktivitaet.
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import threading
import time
from datetime import datetime
import os
import json

PROXY_LOG = r"C:\Users\chris\.grok\proxy\logs\proxy.log"
PORT = 18743

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
        self.root.title("PROXY LIVE STATUS")
        self.root.geometry("700x420")
        self.root.resizable(True, True)
        
        # Immer oben (kann man togglen)
        self.always_on_top = tk.BooleanVar(value=True)
        self.root.attributes("-topmost", True)
        self.root.geometry("550x320")
        
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
            font=("Consolas", 10, "bold"),
            fg="#00ff00",
            bg="#003300"
        )
        self.datenklau_banner.pack(fill="x", padx=5, pady=(0,5))
        
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
        
        tk.Label(log_frame, text="Letzte Aktivitaet (Proxy-Log):", fg="#ccc").pack(anchor="w")
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=16, 
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#00ff00",
            insertbackground="white"
        )
        self.log_text.pack(fill="both", expand=True)

        # Hinweis für Steuerung
        tk.Label(log_frame, text="Mit den Buttons unten kannst du den Proxy starten/stoppen.", fg="#888").pack(anchor="w")
        
        # Buttons
        btn_frame = tk.Frame(root)
        btn_frame.pack(fill="x", padx=5, pady=5)
        
        tk.Button(btn_frame, text="Proxy starten", command=self.start_proxy).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Proxy stoppen", command=self.stop_proxy).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Einstellungen", command=self.open_settings).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Jetzt aktualisieren", command=self.update_now).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Fenster schließen", command=root.destroy).pack(side="right", padx=5)
        
        # Start auto refresh
        self.running = True
        self.current_pid = "?"
        self.protection_active = False
        self.thread = threading.Thread(target=self.auto_refresh, daemon=True)
        self.thread.start()
        
        # Erster Update
        self.update_now()
    
    def toggle_topmost(self):
        self.root.attributes("-topmost", self.always_on_top.get())

    def check_data_theft_protection(self):
        """Prüft, ob alle kritischen Datenklau-Pfade in deny_prefixes sind."""
        policy_path = r"C:\Users\chris\.grok\proxy\policy.json"
        try:
            with open(policy_path, "r", encoding="utf-8") as f:
                policy = json.load(f)
            deny = set(policy.get("deny_prefixes", []))
            missing = [p for p in CRITICAL_DATA_THEFT_DENY if p not in deny]
            self.protection_active = len(missing) == 0
            return missing
        except Exception:
            self.protection_active = False
            return CRITICAL_DATA_THEFT_DENY[:]
    
    def update_now(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=now)
        
        # Port Status
        try:
            result = subprocess.run(
                ["netstat", "-ano"], 
                capture_output=True, 
                text=True, 
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            lines = [l for l in result.stdout.splitlines() if f":{PORT}" in l]
            # Robuste Erkennung: die Listening-Zeile hat typisch "0.0.0.0:0" als Foreign Address (sprachunabhängig)
            listening = any("0.0.0.0:0" in l or "::" in l for l in lines)
            
            if listening:
                pid = "?"
                for l in lines:
                    if "0.0.0.0:0" in l or "::" in l:  # nur die echte Listening-Zeile
                        parts = l.strip().split()
                        if parts:
                            pid = parts[-1]
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
        except Exception as e:
            self.status_label.config(text=f"FEHLER: {e}", fg="#ff8800")
            self.protection_label.config(text="DATENKLAU-SCHUTZ: FEHLER", fg="#ff8800")
        
        # Log Eintraege
        if os.path.exists(PROXY_LOG):
            try:
                with open(PROXY_LOG, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()[-10:]  # letzte 10 Zeilen
                
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

    def start_proxy(self):
        # Vor dem Start: Sicherstellen dass voller Datenklau-Schutz aktiv ist
        missing = self.check_data_theft_protection()
        if not self.protection_active:
            # Auto-aktivieren des vollen Schutzes
            policy_path = r"C:\Users\chris\.grok\proxy\policy.json"
            try:
                with open(policy_path, "r", encoding="utf-8") as f:
                    policy = json.load(f)
                deny = set(policy.get("deny_prefixes", []))
                for p in CRITICAL_DATA_THEFT_DENY:
                    deny.add(p)
                policy["deny_prefixes"] = sorted(list(deny))
                with open(policy_path, "w", encoding="utf-8") as f:
                    json.dump(policy, f, indent=2, ensure_ascii=False)
                self.protection_active = True
            except:
                pass

        proxy = r"C:\Users\chris\.grok\proxy\xai_filter_proxy.py"
        try:
            # Versuche py -3 wie in den Start-Skripten
            subprocess.Popen(["py", "-3", proxy], creationflags=subprocess.CREATE_NO_WINDOW)
            self.root.after(2000, self.update_now)
        except FileNotFoundError:
            try:
                subprocess.Popen(["python", proxy], creationflags=subprocess.CREATE_NO_WINDOW)
                self.root.after(2000, self.update_now)
            except Exception as e:
                self.status_label.config(text=f"START FEHLER: {e}", fg="#ff8800")
        except Exception as e:
            self.status_label.config(text=f"START FEHLER: {e}", fg="#ff8800")

    def stop_proxy(self):
        if self.current_pid and self.current_pid.isdigit():
            try:
                subprocess.call(["taskkill", "/PID", self.current_pid, "/F"], creationflags=subprocess.CREATE_NO_WINDOW)
                self.root.after(1500, self.update_now)
            except Exception as e:
                self.status_label.config(text=f"STOP FEHLER: {e}", fg="#ff8800")

    def open_settings(self):
        """Öffnet ein Einstellungsfenster für die Proxy-Policy.
        Fokus: Einfache Kontrolle gegen Datenklau (Exfiltration).
        """
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Proxy Einstellungen")
        settings_win.geometry("650x580")
        settings_win.resizable(True, True)

        # Policy laden
        policy_path = r"C:\Users\chris\.grok\proxy\policy.json"
        try:
            with open(policy_path, "r", encoding="utf-8") as f:
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
        tk.Button(btns, text="Speichern", command=lambda: self._save_policy(settings_win, policy_path)).pack(side="left", padx=5)
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

    def _save_policy(self, win, path):
        try:
            new_policy = {
                "version": 1,
                "comment": "Default-deny. Nur was Grok zum Arbeiten braucht. Bei Chat-403: BLOCK-Log pruefen und hier vorsichtig ergaenzen.",
                "upstream_host": "cli-chat-proxy.grok.com",
                "upstream_port": 443,
                "allow_prefixes": list(self.allow_list.get(0, "end")),
                "allow_get_only_prefixes": policy.get("allow_get_only_prefixes", []),
                "deny_prefixes": (lambda d: d + [p for p in CRITICAL_DATA_THEFT_DENY if self.datenklau_var.get() and p not in d])(list(self.deny_list.get(0, "end"))),
                "block_git_bundle_bodies": self.block_git.get(),
                "block_pack_magic_bodies": self.block_pack.get(),
                "max_body_gzip_bytes": int(self.max_gzip.get() or 256000),
                "log_max_bytes": int(self.log_max.get() or 5242880),
                "log_backup_count": int(self.log_backup.get() or 5)
            }

            with open(path, "w", encoding="utf-8") as f:
                json.dump(new_policy, f, indent=2, ensure_ascii=False)

            messagebox.showinfo("Gespeichert", "Policy gespeichert.\nProxy neu starten für Übernahme der Änderungen.")
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
