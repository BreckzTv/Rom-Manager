#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rom_Manager_full.py
Umfassender ROM-Manager mit:
 - JSON & SQLite Backend
 - Tkinter-GUI (Listen, Doppelklick, Drag & Drop)
 - Batch Pfad-Assistent (Remap)
 - FastAPI Remote-API (optional)
 - Multithreaded SHA1-Checks mit Fortschritt (tqdm / GUI)
 - Export für RetroArch & EmulationStation
Usage:
  python Rom_Manager_full.py         # CLI (text)
  python Rom_Manager_full.py --gui   # Start GUI
  python Rom_Manager_full.py --sqlite mydb.sqlite  # Use sqlite file
"""

import os
import sys
import json
import hashlib
import csv
import sqlite3
import threading
import subprocess
import platform
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Tuple, Dict, Iterable

# Optional libs
try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)
except Exception:
    class _NoColor:
        def __getattr__(self, name): return ""
    Fore = Style = _NoColor()

try:
    from tqdm import tqdm
except Exception:
    tqdm = None  # fallback: keine Fortschrittsanzeige in CLI

# FastAPI (optional)
try:
    from fastapi import FastAPI
    from pydantic import BaseModel
    import uvicorn
    FASTAPI_AVAILABLE = True
except Exception:
    FASTAPI_AVAILABLE = False

# Tkinter GUI (optional)
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    TK_AVAILABLE = True
except Exception:
    TK_AVAILABLE = False

# -------------------------
# Hilfsfunktionen
# -------------------------
def human_size(num_bytes: int) -> str:
    for unit in ['B','KB','MB','GB','TB']:
        if num_bytes < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"

def parse_date(s: Optional[str]) -> Optional[datetime]:
    if not s: return None
    if isinstance(s, datetime): return s
    s = s.strip()
    try:
        return datetime.fromisoformat(s)
    except Exception:
        pass
    fmts = ["%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d.%m.%Y"]
    for f in fmts:
        try:
            return datetime.strptime(s, f)
        except Exception:
            continue
    try:
        n = float(s); return datetime.fromtimestamp(n)
    except Exception:
        return None

def calc_sha1_of_file(path: str, chunk_size: int = 1024*1024) -> str:
    sha1 = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha1.update(chunk)
    return sha1.hexdigest()

def open_in_explorer(path: str):
    try:
        p = Path(path)
        if p.is_file():
            if platform.system() == "Windows":
                subprocess.run(["explorer", "/select,", str(p)])
            elif platform.system() == "Darwin":
                subprocess.run(["open", "-R", str(p)])
            else:
                subprocess.run(["xdg-open", str(p.parent)])
        else:
            if platform.system() == "Windows":
                subprocess.run(["explorer", str(path)])
            elif platform.system() == "Darwin":
                subprocess.run(["open", str(path)])
            else:
                subprocess.run(["xdg-open", str(path)])
    except Exception as e:
        print("Fehler beim Öffnen des Explorers:", e)

# -------------------------
# Datenmodelle
# -------------------------
class Rom:
    def __init__(self, name, path, size=0, size_h=None, sha1="", added=None):
        self.name = name
        self.path = path
        self.size = int(size) if size else 0
        self.size_h = size_h or human_size(self.size)
        self.sha1 = sha1 or ""
        self.added = parse_date(added)

    def exists(self) -> bool:
        return Path(self.path).exists()

    def verify_sha1(self) -> Tuple[bool, Optional[str]]:
        if not self.exists(): return False, None
        try:
            c = calc_sha1_of_file(self.path)
            return c.lower() == (self.sha1 or "").lower(), c
        except Exception:
            return False, None

    def to_dict(self):
        return {"name": self.name, "path": self.path, "size": self.size, "size_h": self.size_h, "sha1": self.sha1, "added": self.added.isoformat() if self.added else None}

    def __repr__(self):
        return f"<Rom {self.name} {self.size_h}>"

class RomCollection:
    def __init__(self):
        self.data: Dict[str, List[Rom]] = defaultdict(list)

    # JSON load/save
    def load_json(self, filename="Data.json"):
        if not Path(filename).exists():
            raise FileNotFoundError(filename)
        with open(filename, "r", encoding="utf-8") as f:
            raw = json.load(f)
        self.data.clear()
        for console, roms in raw.items():
            for r in roms:
                name = r.get("name") or r.get("title") or "UNNAMED"
                path = r.get("path") or ""
                size = r.get("size") or 0
                size_h = r.get("size_h") or human_size(int(size) if size else 0)
                sha1 = r.get("sha1") or ""
                added = r.get("added") or None
                self.data[console].append(Rom(name, path, size, size_h, sha1, added))

    def save_json(self, filename="Data.json"):
        out = {console: [r.to_dict() for r in roms] for console, roms in self.data.items()}
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)

    # SQLite backend
    def init_sqlite(self, db_path="roms.db"):
        self.sqlite_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS roms (
                id INTEGER PRIMARY KEY,
                console TEXT,
                name TEXT,
                path TEXT,
                size INTEGER,
                size_h TEXT,
                sha1 TEXT,
                added TEXT
            )
        """)
        self.conn.commit()

    def migrate_json_to_sqlite(self, json_file="Data.json"):
        self.load_json(json_file)
        if not hasattr(self, 'conn'):
            raise RuntimeError("SQLite nicht initialisiert")
        cur = self.conn.cursor()
        cur.execute("DELETE FROM roms")
        for console, roms in self.data.items():
            for r in roms:
                cur.execute("INSERT INTO roms (console,name,path,size,size_h,sha1,added) VALUES (?,?,?,?,?,?,?)",
                            (console, r.name, r.path, r.size, r.size_h, r.sha1, r.added.isoformat() if r.added else None))
        self.conn.commit()

    def load_from_sqlite(self, db_path="roms.db"):
        self.init_sqlite(db_path)
        cur = self.conn.cursor()
        cur.execute("SELECT console,name,path,size,size_h,sha1,added FROM roms")
        self.data.clear()
        for console,name,path,size,size_h,sha1,added in cur.fetchall():
            self.data[console].append(Rom(name,path,size,size_h,sha1,added))

    def save_to_sqlite(self, db_path="roms.db"):
        if not hasattr(self, 'conn'):
            self.init_sqlite(db_path)
        cur = self.conn.cursor()
        cur.execute("DELETE FROM roms")
        for console,roms in self.data.items():
            for r in roms:
                cur.execute("INSERT INTO roms (console,name,path,size,size_h,sha1,added) VALUES (?,?,?,?,?,?,?)",
                            (console, r.name, r.path, r.size, r.size_h, r.sha1, r.added.isoformat() if r.added else None))
        self.conn.commit()

    # Iteration
    def iter_all(self) -> Iterable[Tuple[str, Rom]]:
        for console,roms in self.data.items():
            for r in roms:
                yield console, r

    # Suche & Filter
    def search_by_name(self, keyword):
        kw = keyword.lower()
        return [(c,r) for c,r in self.iter_all() if kw in (r.name or "").lower()]

    def filter_by_console(self, console):
        return self.data.get(console, [])

    def find_missing_files(self):
        return [(c,r) for c,r in self.iter_all() if not r.exists()]

    def check_all_sha1_threaded(self, max_workers=6, only_mismatch=True, gui_progress_callback=None):
        items = list(self.iter_all())
        results = []
        # use ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(r.verify_sha1): (c,r) for (c,r) in items}
            if tqdm and gui_progress_callback is None:
                for f in tqdm(as_completed(futures), total=len(futures)):
                    c,r = futures[f]
                    try:
                        match, computed = f.result()
                    except Exception:
                        match, computed = False, None
                    if not only_mismatch or not match:
                        results.append((c,r,match,computed))
            else:
                # no tqdm or GUI; simple loop and optional GUI callback
                completed = 0
                total = len(futures)
                for future in as_completed(futures):
                    c,r = futures[future]
                    try:
                        match, computed = future.result()
                    except Exception:
                        match, computed = False, None
                    if not only_mismatch or not match:
                        results.append((c,r,match,computed))
                    completed += 1
                    if gui_progress_callback:
                        gui_progress_callback(completed, total)
        return results

    # Exports
    def export_csv(self, filename="roms_export.csv"):
        header = ["console","name","path","size","size_h","sha1","added"]
        with open(filename,"w",encoding="utf-8",newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            for c,r in self.iter_all():
                w.writerow([c,r.name,r.path,r.size,r.size_h,r.sha1, r.added.isoformat() if r.added else ""])
        return filename

    def export_json(self, filename="roms_export.json"):
        out = {console:[r.to_dict() for r in roms] for console,roms in self.data.items()}
        with open(filename,"w",encoding="utf-8") as f:
            json.dump(out,f,indent=2,ensure_ascii=False)
        return filename

    def export_retroarch_lpl(self, console, filename=None):
        # RetroArch .lpl is typically a JSON list of entries; here produce a simple JSON playlist
        import json as _json
        entries = []
        for r in self.data.get(console, []):
            entries.append({
                "path": r.path,
                "label": r.name,
                "core_path": "",
                "crc32": "",
                "db_name": "",
                "rom_id": "",
                "rating": 0,
                "last_played": ""
            })
        if not filename:
            filename = f"{console}.lpl"
        with open(filename,"w",encoding="utf-8") as f:
            _json.dump(entries,f,indent=2,ensure_ascii=False)
        return filename

    def export_emulationstation_csv(self, filename="emulationstation_export.csv"):
        header = ["console","name","path","size","sha1","added"]
        with open(filename,"w",encoding="utf-8",newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            for c,r in self.iter_all():
                w.writerow([c,r.name,r.path,r.size,r.sha1, r.added.isoformat() if r.added else ""])
        return filename

    # Batch Pfad-Remapper (heuristiken)
    def suggest_path_remap(self, missing_root_candidates: List[str], search_roots: List[str], max_hits=3):
        """
        Versucht per heuristischer Suche Vorschläge für fehlende Dateien.
        - missing_root_candidates: Liste mit (zu ersetzendem) Strings oder Mustern
        - search_roots: List von Pfaden (Root-Ordnern) die durchsucht werden sollen
        Retourniert mapping dict: original_subpath -> new_fullpath
        Achtung: kann lange dauern bei großen search_roots.
        """
        missing = self.find_missing_files()
        suggestions = {}  # (console,rom) -> [possible_path,...]
        for c,r in missing:
            candidates = []
            filename = Path(r.path).name
            # Durchsuche search_roots nach Dateien mit gleichem Dateinamen
            for root in search_roots:
                rootp = Path(root)
                if not rootp.exists(): continue
                # walk; Abbruch nach max_hits Vorschlägen
                for p in rootp.rglob(filename):
                    candidates.append(str(p))
                    if len(candidates) >= max_hits:
                        break
                if len(candidates) >= max_hits:
                    break
            # Falls noch leer: versuche einfache Ersetzungen der Root-Strings
            if not candidates and missing_root_candidates:
                orig_path = r.path
                for pattern in missing_root_candidates:
                    for replacement in missing_root_candidates:
                        if pattern == replacement: continue
                        newpath = orig_path.replace(pattern, replacement)
                        if Path(newpath).exists():
                            candidates.append(newpath)
            suggestions[(c,r.path)] = candidates
        return suggestions

    def apply_remap(self, remap_dict: Dict[str,str]):
        """
        remap_dict: old_fullpath -> new_fullpath
        Aktualisiert die entsprechende ROM-Einträge in-place (Pfad und evtl. size/sha1/size_h)
        """
        changed = 0
        for c,r in self.iter_all():
            if r.path in remap_dict:
                new = remap_dict[r.path]
                r.path = new
                try:
                    s = Path(new).stat().st_size
                    r.size = int(s)
                    r.size_h = human_size(r.size)
                except Exception:
                    pass
                changed += 1
        return changed

# -------------------------
# Manager & CLI / GUI
# -------------------------
class RomManager:
    def __init__(self, data_json="Data.json", sqlite_path:Optional[str]=None):
        self.collection = RomCollection()
        self.data_json = data_json
        self.sqlite_path = sqlite_path
        self.api_thread = None
        self.api_app = None
        self.api_port = 8000

    def load(self):
        if self.sqlite_path:
            if Path(self.sqlite_path).exists():
                self.collection.load_from_sqlite(self.sqlite_path)
            else:
                # migrate from JSON if present
                if Path(self.data_json).exists():
                    self.collection.migrate_json_to_sqlite(self.data_json)
                    self.collection.load_from_sqlite(self.sqlite_path)
                else:
                    raise FileNotFoundError("Weder sqlite noch Data.json gefunden")
        else:
            self.collection.load_json(self.data_json)

    def save(self):
        if self.sqlite_path:
            self.collection.save_to_sqlite(self.sqlite_path)
        else:
            self.collection.save_json(self.data_json)

    # CLI helpers
    def show_stats(self):
        stats = {}
        total_count = 0
        total_bytes = 0
        for c, roms in self.collection.data.items():
            count = len(roms)
            sizes = [r.size for r in roms if r.size]
            total = sum(sizes) if sizes else 0
            largest = max(roms, key=lambda x: x.size) if roms else None
            oldest = min([r for r in roms if r.added], key=lambda x: x.added) if any(r.added for r in roms) else None
            stats[c] = {"count":count, "total_h":human_size(total), "largest":(largest.name if largest else None, human_size(largest.size) if largest else None),"oldest":(oldest.name if oldest else None, oldest.added.isoformat() if oldest else None)}
            total_count += count
            total_bytes += total
        print("=== Statistik ===")
        for c,s in stats.items():
            print(f"{c}: {s['count']} Spiele, Gesamt: {s['total_h']}, größtes: {s['largest'][0]} ({s['largest'][1]}), ältestes: {s['oldest'][0]} ({s['oldest'][1]})")
        print(f"Total: {total_count} Spiele, Gesamtgröße: {human_size(total_bytes)}")

    def start_api(self, host="127.0.0.1", port:int=8000):
        if not FASTAPI_AVAILABLE:
            print("FastAPI/uvicorn nicht installiert.")
            return
        app = FastAPI()
        self.api_app = app
        mgr = self

        class RomModel(BaseModel):
            console: str
            name: str
            path: str
            size: int
            size_h: str
            sha1: str
            added: Optional[str]

        @app.get("/status")
        def status():
            return {"status":"ok", "total": sum(len(v) for v in mgr.collection.data.values())}

        @app.get("/list")
        def list_all():
            out = {console:[r.to_dict() for r in roms] for console,roms in mgr.collection.data.items()}
            return out

        @app.get("/search")
        def api_search(name: str):
            res = mgr.collection.search_by_name(name)
            return [{ "console": c, **r.to_dict() } for c,r in res]

        @app.get("/export")
        def api_export(format: str = "csv"):
            if format == "csv":
                fn = mgr.collection.export_csv("api_export.csv")
                return {"file":fn}
            elif format == "json":
                fn = mgr.collection.export_json("api_export.json")
                return {"file":fn}
            else:
                return {"error":"unsupported"}

        def run_uvicorn():
            uvicorn.run(app, host=host, port=port)

        t = threading.Thread(target=run_uvicorn, daemon=True)
        t.start()
        self.api_thread = t
        self.api_port = port
        print(f"API gestartet auf http://{host}:{port}")

    # CLI SHA1 Check (multithreaded)
    def check_sha1_cli(self, only_mismatch=True, workers=6):
        print("Starte SHA1-Checks (multithreaded)...")
        results = self.collection.check_all_sha1_threaded(max_workers=workers, only_mismatch=only_mismatch, gui_progress_callback=None)
        mismatches = [r for r in results if not r[2]]
        print(f"Ergebnis: geprüfte Einträge: {len(results)}; mismatches: {len(mismatches)}")
        for c,r,match,comp in results:
            status = "OK" if match else "MISMATCH"
            print(f"[{c}] {r.name} | gespeicherte: {(r.sha1 or '')[:12]} | computed: {(comp or '')[:12]} | {status}")

    # Batch remap helper (CLI)
    def batch_remap_interactive(self, search_roots):
        suggestions = self.collection.suggest_path_remap([], search_roots, max_hits=5)
        remap = {}
        for (console,oldpath), candidates in suggestions.items():
            if not candidates:
                print(f"[{console}] {oldpath} -> keine Vorschläge")
                continue
            print(f"[{console}] {oldpath} -> Vorschläge:")
            for i,cand in enumerate(candidates):
                print(f"  {i}) {cand}")
            sel = input("Wähle Index (-1 skip, a = enter manuell): ").strip()
            if sel == "-1" or sel == "":
                continue
            if sel.lower() == "a":
                manual = input("Gib neuen Pfad ein: ").strip()
                if manual and Path(manual).exists():
                    remap[oldpath] = manual
            else:
                try:
                    idx = int(sel)
                    if 0 <= idx < len(candidates):
                        remap[oldpath] = candidates[idx]
                except Exception:
                    pass
        if remap:
            changed = self.collection.apply_remap(remap)
            print(f"Angewendet: {changed} Einträge geändert")
        else:
            print("Keine Änderungen vorgenommen.")

# -------------------------
# GUI (Tkinter) - einfach, funktional
# -------------------------
if TK_AVAILABLE:
    class RomManagerGUI:
        def __init__(self, manager: RomManager):
            self.mgr = manager
            self.root = tk.Tk()
            self.root.title("ROM Manager (GUI)")
            self.root.geometry("1000x600")
            self.create_widgets()
            # load data
            try:
                self.mgr.load()
            except Exception as e:
                messagebox.showwarning("Laden fehlgeschlagen", f"Fehler: {e}")
            self.populate_consoles()

        def create_widgets(self):
            # left: console list
            left = ttk.Frame(self.root, padding=6)
            left.pack(side=tk.LEFT, fill=tk.Y)
            ttk.Label(left, text="Konsolen").pack(anchor=tk.W)
            self.console_listbox = tk.Listbox(left, width=20)
            self.console_listbox.pack(fill=tk.Y, expand=True)
            self.console_listbox.bind("<<ListboxSelect>>", self.on_console_select)

            # middle: treeview for roms
            mid = ttk.Frame(self.root, padding=6)
            mid.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            cols = ("name","size","sha1","status")
            self.tree = ttk.Treeview(mid, columns=cols, show="headings")
            for c in cols:
                self.tree.heading(c, text=c.capitalize())
                self.tree.column(c, width=200 if c=="name" else 100)
            self.tree.pack(fill=tk.BOTH, expand=True)
            self.tree.bind("<Double-1>", self.on_rom_double_click)

            # right: details & actions
            right = ttk.Frame(self.root, padding=6)
            right.pack(side=tk.RIGHT, fill=tk.Y)
            ttk.Label(right, text="Aktionen").pack()
            ttk.Button(right, text="SHA1 Prüfen (Parallel)", command=self.gui_sha1_check).pack(fill=tk.X, pady=4)
            ttk.Button(right, text="Fehlende Dateien anzeigen", command=self.gui_show_missing).pack(fill=tk.X, pady=4)
            ttk.Button(right, text="Batch Remap (Heuristik)", command=self.gui_batch_remap).pack(fill=tk.X, pady=4)
            ttk.Button(right, text="Export: CSV", command=self.gui_export_csv).pack(fill=tk.X, pady=4)
            ttk.Button(right, text="Start API", command=self.gui_start_api).pack(fill=tk.X, pady=4)

            # progress
            self.progress = ttk.Progressbar(self.root, orient="horizontal", mode="determinate")
            self.progress.pack(fill=tk.X, side=tk.BOTTOM)

        def populate_consoles(self):
            self.console_listbox.delete(0, tk.END)
            consoles = list(self.mgr.collection.data.keys())
            for c in consoles:
                self.console_listbox.insert(tk.END, c)

        def on_console_select(self, event):
            sel = self.console_listbox.curselection()
            if not sel: return
            idx = sel[0]
            console = self.console_listbox.get(idx)
            self.populate_roms(console)

        def populate_roms(self, console):
            for i in self.tree.get_children():
                self.tree.delete(i)
            roms = self.mgr.collection.filter_by_console(console)
            for r in roms:
                status = "OK" if r.exists() else "MISSING"
                self.tree.insert("", tk.END, values=(r.name, r.size_h, r.sha1[:10] if r.sha1 else "", status))

        def on_rom_double_click(self, event):
            item = self.tree.identify_row(event.y)
            if not item: return
            vals = self.tree.item(item,"values")
            name = vals[0]
            # find rom by name in current console
            sel = self.console_listbox.curselection()
            if not sel: return
            console = self.console_listbox.get(sel[0])
            roms = [r for r in self.mgr.collection.filter_by_console(console) if r.name == name]
            if not roms:
                return
            rom = roms[0]
            if Path(rom.path).exists():
                open_in_explorer(rom.path)
            else:
                messagebox.showinfo("Datei fehlt", f"Pfad existiert nicht:\n{rom.path}")

        def gui_sha1_check(self):
            def progress_cb(done, total):
                self.progress['maximum'] = total
                self.progress['value'] = done
                self.root.update_idletasks()

            def run_check():
                self.progress['value'] = 0
                results = self.mgr.collection.check_all_sha1_threaded(max_workers=6, only_mismatch=False, gui_progress_callback=progress_cb)
                # zeige in modal
                mismatches = [t for t in results if not t[2]]
                messagebox.showinfo("SHA1-Prüfung", f"Prüfung fertig. Einträge: {len(results)}, Mismatches: {len(mismatches)}")
                self.progress['value'] = 0

            threading.Thread(target=run_check, daemon=True).start()

        def gui_show_missing(self):
            missing = self.mgr.collection.find_missing_files()
            out = "\n".join([f"[{c}] {r.name} -> {r.path}" for c,r in missing])
            if not out: out = "Keine fehlenden Dateien."
            # show in scrolled window
            win = tk.Toplevel(self.root)
            win.title("Fehlende Dateien")
            txt = tk.Text(win, wrap="none")
            txt.insert("1.0", out)
            txt.pack(fill=tk.BOTH, expand=True)

        def gui_batch_remap(self):
            # ask for search roots
            roots = filedialog.askdirectory(title="Wurzelordner zum Durchsuchen (wiederholt wählen nicht möglich im Dialog) --- wenn mehrere Root-Ordner benötigt werden, wiederhole den Vorgang")
            if not roots:
                return
            # run suggestions
            def run():
                self.progress['value'] = 0
                suggestions = self.mgr.collection.suggest_path_remap([], [roots], max_hits=5)
                # show small selector window to accept suggestions
                selwin = tk.Toplevel(self.root)
                selwin.title("Remap Vorschläge")
                lb = tk.Listbox(selwin, width=120)
                lb.pack(fill=tk.BOTH, expand=True)
                mapping = {}
                keys = list(suggestions.keys())
                for i,k in enumerate(keys):
                    console, oldpath = k
                    cand = suggestions[k]
                    if cand:
                        line = f"[{console}] {oldpath} => {cand[0]}"
                        mapping[oldpath] = cand[0]
                    else:
                        line = f"[{console}] {oldpath} => (keine Vorschläge)"
                    lb.insert(tk.END, line)
                def apply():
                    changed = self.mgr.collection.apply_remap(mapping)
                    messagebox.showinfo("Remap", f"{changed} Einträge geändert")
                    selwin.destroy()
                ttk.Button(selwin, text="Anwenden (automatisch Vorschlag verwenden)", command=apply).pack()
            threading.Thread(target=run, daemon=True).start()

        def gui_export_csv(self):
            fn = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")])
            if not fn: return
            self.mgr.collection.export_csv(fn)
            messagebox.showinfo("Export", f"Exportiert: {fn}")

        def gui_start_api(self):
            port = 8000
            t = threading.Thread(target=lambda: self.mgr.start_api(port=port), daemon=True)
            t.start()
            messagebox.showinfo("API", f"Starte API auf Port {port}")

        def run(self):
            self.root.mainloop()

# -------------------------
# CLI entrypoint
# -------------------------
def parse_args(argv):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--gui", action="store_true", help="Starte Tkinter GUI")
    ap.add_argument("--sqlite", type=str, default=None, help="Verwende sqlite DB Datei")
    ap.add_argument("--data", type=str, default="Data.json", help="Data.json Pfad")
    ap.add_argument("--sha1-check", action="store_true", help="Starte SHA1 Check (CLI, multithread)")
    ap.add_argument("--api", action="store_true", help="Starte FastAPI Server (benötigt fastapi/uvicorn)")
    ap.add_argument("--export", choices=["csv","json","retroarch","emulation"], help="Export Format (CLI)")
    return ap.parse_args(argv[1:])

def main(argv):
    args = parse_args(argv)
    mgr = RomManager(data_json=args.data, sqlite_path=args.sqlite)
    if args.gui:
        if not TK_AVAILABLE:
            print("Tkinter nicht verfügbar; installiere tkinter oder entferne --gui")
            return
        gui = RomManagerGUI(mgr)
        gui.run()
        return

    # CLI mode
    try:
        mgr.load()
    except Exception as e:
        print(Fore.YELLOW + f"Warnung beim Laden: {e}" + Style.RESET_ALL)
    if args.sha1_check:
        mgr.check_sha1_cli()
    if args.api:
        mgr.start_api()
        input("API läuft. Enter zum Beenden...\n")
    if args.export:
        if args.export == "csv":
            print("Exportiere CSV -> roms_export.csv")
            mgr.collection.export_csv("roms_export.csv")
        elif args.export == "json":
            mgr.collection.export_json("roms_export.json")
        elif args.export == "retroarch":
            consoles = list(mgr.collection.data.keys())
            for c in consoles:
                fname = mgr.collection.export_retroarch_lpl(c, f"{c}.lpl")
                print("Exportiert:", fname)
        elif args.export == "emulation":
            mgr.collection.export_emulationstation_csv("emulation_export.csv")
            print("Exportiert: emulation_export.csv")
    if not any([args.sha1_check, args.api, args.export, args.gui]):
        # interactive CLI
        print("ROM Manager (CLI). Befehle: stats, list <console>, missing, sha1, export <csv/json/retroarch/emulation>, remap, save, quit")
        while True:
            cmd = input("> ").strip().split()
            if not cmd: continue
            c0 = cmd[0].lower()
            if c0 in ("quit","exit","q"):
                break
            if c0 == "stats":
                mgr.show_stats()
            elif c0 == "list":
                if len(cmd) < 2:
                    print("Usage: list <console>")
                else:
                    console = cmd[1]
                    roms = mgr.collection.filter_by_console(console)
                    for r in roms:
                        print(r.name, r.path, r.size_h, "OK" if r.exists() else "MISSING")
            elif c0 == "missing":
                missing = mgr.collection.find_missing_files()
                for c,r in missing:
                    print(f"[{c}] {r.name} -> {r.path}")
            elif c0 == "sha1":
                mgr.check_sha1_cli()
            elif c0 == "export":
                if len(cmd) < 2:
                    print("export csv/json/retroarch/emulation")
                else:
                    fmt = cmd[1]
                    if fmt == "csv":
                        mgr.collection.export_csv("roms_export.csv"); print("Exportiert: roms_export.csv")
                    elif fmt == "json":
                        mgr.collection.export_json("roms_export.json"); print("Exportiert: roms_export.json")
                    elif fmt == "retroarch":
                        for c in mgr.collection.data.keys():
                            mgr.collection.export_retroarch_lpl(c, f"{c}.lpl"); print("Export für", c)
                    elif fmt == "emulation":
                        mgr.collection.export_emulationstation_csv("emulation_export.csv"); print("Exportiert")
            elif c0 == "remap":
                roots = input("Space-getrennte Root-Ordner zum Durchsuchen (z.B. H:\\Archive C:\\Games): ").strip().split()
                mgr.batch_remap_interactive(roots)
            elif c0 == "save":
                mgr.save(); print("Gespeichert.")
            else:
                print("Unbekannter Befehl.")
    # Ende main

if __name__ == "__main__":
    main(sys.argv)
