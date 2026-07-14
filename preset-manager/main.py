import json
import sys
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from urllib import error, request

from config import BACKUP_ROOT, create_preset_store, load_config, save_config
from server import PresetApiServer


def flask_available() -> bool:
    try:
        import flask  # noqa: F401
        return True
    except ImportError:
        return False


class PresetManagerApp:
    def __init__(self):
        self.config = load_config()
        self.root = tk.Tk()
        self.root.title("mt17 Presets")
        self.root.geometry("520x580")
        self.root.minsize(480, 520)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.store = create_preset_store(self.config)
        self.port = int(self.config.get("apiPort", 8766))
        self.api_base = f"http://127.0.0.1:{self.port}"
        self.server = PresetApiServer(self.store, port=self.port)
        self.server.start()

        self.presets = []
        self._busy = False
        self._wait_action = None
        self._wait_deadline = 0.0
        self._wait_label = ""
        self._wait_file = ""
        self._wait_name = ""
        self._action_buttons = []

        self._build_ui()
        self.refresh_list()
        self.root.after(1000, self.poll_health)

    def _build_ui(self):
        shell = ttk.Frame(self.root, padding=12)
        shell.grid(row=0, column=0, sticky="nsew")
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(3, weight=1)

        ttk.Label(
            shell,
            text="mt17 Preset Manager",
            font=("Segoe UI", 16, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            shell,
            text="1) Tune wallpaper in Lively  2) Save or Apply presets here",
            wraplength=460,
        ).grid(row=1, column=0, sticky="w", pady=(4, 8))

        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(
            shell,
            textvariable=self.status_var,
            foreground="#006400",
            wraplength=460,
        )
        self.status_label.grid(row=2, column=0, sticky="nw", pady=(0, 8))

        list_frame = ttk.Frame(shell)
        list_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 8))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        shell.rowconfigure(3, weight=1)

        ttk.Label(list_frame, text="Your presets").grid(row=0, column=0, sticky="w")

        box_frame = ttk.Frame(list_frame)
        box_frame.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        box_frame.columnconfigure(0, weight=1)
        box_frame.rowconfigure(0, weight=1)
        list_frame.rowconfigure(1, weight=1)

        self.listbox = tk.Listbox(
            box_frame,
            font=("Segoe UI", 11),
            activestyle="none",
            exportselection=False,
        )
        self.listbox.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(box_frame, orient="vertical", command=self.listbox.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.listbox.configure(yscrollcommand=scroll.set)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        ttk.Label(shell, text="Preset name").grid(row=4, column=0, sticky="w")
        self.name_var = tk.StringVar()
        ttk.Entry(shell, textvariable=self.name_var, font=("Segoe UI", 11)).grid(
            row=5, column=0, sticky="ew", pady=(4, 8)
        )

        ttk.Label(shell, text="Lively monitor (saved settings)").grid(row=6, column=0, sticky="w")
        self.monitor_var = tk.StringVar(value=self.config.get("targetMonitor", "1"))
        self.monitor_combo = ttk.Combobox(
            shell,
            textvariable=self.monitor_var,
            state="readonly",
            font=("Segoe UI", 11),
        )
        self.monitor_combo.grid(row=7, column=0, sticky="ew", pady=(4, 8))
        self.monitor_combo.bind("<<ComboboxSelected>>", self.on_monitor_change)
        self._load_monitors()

        path_info = self.store.lively_sync.path_summary()
        ttk.Label(
            shell,
            text=f"Wallpaper: {path_info.get('installedWallpaperPath', '')}",
            wraplength=460,
            font=("Segoe UI", 8),
            foreground="#666666",
        ).grid(row=8, column=0, sticky="w", pady=(0, 8))

        primary = ttk.Frame(shell)
        primary.grid(row=9, column=0, sticky="ew", pady=(0, 4))
        primary.columnconfigure(0, weight=1)
        primary.columnconfigure(1, weight=1)

        self.apply_btn = ttk.Button(
            primary,
            text="Apply to wallpaper",
            command=self.apply_selected,
        )
        self.apply_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.save_btn = ttk.Button(
            primary,
            text="Save current look",
            command=self.capture_current,
        )
        self.save_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        secondary = ttk.Frame(shell)
        secondary.grid(row=10, column=0, sticky="ew", pady=(0, 4))
        for index, (label, command) in enumerate(
            [
                ("Rename", self.rename_selected),
                ("Delete", self.delete_selected),
                ("Duplicate", self.duplicate_selected),
            ]
        ):
            button = ttk.Button(secondary, text=label, command=command)
            button.grid(row=0, column=index, sticky="ew", padx=2)
            secondary.columnconfigure(index, weight=1)
            self._action_buttons.append(button)

        tools = ttk.Frame(shell)
        tools.grid(row=11, column=0, sticky="ew")
        self.backup_btn = ttk.Button(tools, text="Backup", command=self.backup_all)
        self.backup_btn.pack(side="left", padx=(0, 4))
        self.restore_btn = ttk.Button(
            tools, text="Restore backup", command=self.restore_backup
        )
        self.restore_btn.pack(side="left", padx=(0, 4))
        ttk.Button(tools, text="Settings", command=self.open_settings).pack(side="right")

        self._action_buttons.extend(
            [self.apply_btn, self.save_btn, self.backup_btn, self.restore_btn]
        )

    def selected_entry(self) -> dict | None:
        selection = self.listbox.curselection()
        if not selection:
            return None
        return self.presets[selection[0]]

    def on_select(self, _event=None):
        entry = self.selected_entry()
        if entry:
            self.name_var.set(entry["name"])

    def refresh_list(
        self,
        select_name: str | None = None,
        select_file: str | None = None,
        message: str | None = None,
    ):
        self.presets = self.store.list_presets()
        self.listbox.delete(0, tk.END)
        select_index = None
        for index, preset in enumerate(self.presets):
            self.listbox.insert(tk.END, preset["name"])
            if select_file and preset["file"] == select_file:
                select_index = index
            elif (
                select_index is None
                and select_name
                and preset["name"].casefold() == select_name.casefold()
            ):
                select_index = index

        if select_index is not None:
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(select_index)
            self.listbox.see(select_index)
            self.name_var.set(self.presets[select_index]["name"])

        if message:
            self.set_status(message)
        elif not self._busy:
            self.set_status(f"{len(self.presets)} preset(s) ready")

    def set_status(self, message: str, ok: bool = True):
        self.status_var.set(message)
        self.status_label.configure(foreground="#006400" if ok else "#a00000")

    def set_busy(self, busy: bool):
        self._busy = busy
        state = "disabled" if busy else "normal"
        for button in self._action_buttons:
            button.configure(state=state)

    def begin_wait(
        self,
        action: str,
        label: str,
        timeout_seconds: int = 15,
        wait_file: str = "",
        wait_name: str = "",
    ):
        self._wait_action = action
        self._wait_label = label
        self._wait_file = wait_file
        self._wait_name = wait_name
        self._wait_deadline = time.time() + timeout_seconds
        self.server.last_status = {"ok": None, "message": "Working...", "action": None}
        self.set_busy(True)
        self.set_status(f"{label}... waiting for wallpaper")
        self.root.after(200, self.poll_wait)

    def poll_wait(self):
        if not self._wait_action:
            return

        if time.time() > self._wait_deadline:
            self.finish_wait(
                f"{self._wait_label} timed out. Reload the wallpaper in Lively once.",
                ok=False,
            )
            return

        status = self.server.last_status
        if status.get("action") != self._wait_action:
            self.root.after(200, self.poll_wait)
            return

        if status.get("ok") is True:
            self.refresh_list(
                select_file=status.get("file") or self._wait_file,
                select_name=status.get("name") or self._wait_name,
            )
            self.finish_wait(status.get("message") or f"{self._wait_label} done")
            return

        if status.get("ok") is False:
            self.finish_wait(status.get("message") or f"{self._wait_label} failed", ok=False)
            return

        self.root.after(200, self.poll_wait)

    def finish_wait(self, message: str, ok: bool = True):
        self._wait_action = None
        self.set_busy(False)
        self.set_status(message, ok=ok)

    def _load_monitors(self):
        monitors = self.store.list_monitors()
        values = [item["id"] for item in monitors] or ["1"]
        self.monitor_combo["values"] = values
        current = self.config.get("targetMonitor", values[0])
        if current not in values:
            current = values[0]
        self.monitor_var.set(current)
        self.store.target_monitor = current

    def on_monitor_change(self, _event=None):
        monitor = self.monitor_var.get().strip()
        if not monitor:
            return
        self.store.target_monitor = monitor
        self.config["targetMonitor"] = monitor
        save_config(self.config)

    def _selected_monitor(self) -> str:
        monitor = self.monitor_var.get().strip()
        return monitor or self.store.target_monitor

    def apply_selected(self):
        if self._busy:
            return

        entry = self.selected_entry()
        if not entry:
            messagebox.showinfo("Apply preset", "Select a preset from the list first.")
            return

        monitor = self._selected_monitor()
        self.store.target_monitor = monitor
        self.config["targetMonitor"] = monitor
        save_config(self.config)

        result = self.store.write_command(
            "apply",
            monitor=monitor,
            name=entry["name"],
            file=entry["file"],
        )
        persistence = result.get("livelyPersistence") or {}
        lively_count = len(result.get("livelySavedataFiles") or [])
        label = f"Applying '{entry['name']}' on monitor {monitor}"
        if persistence.get("attempted") and not persistence.get("ok"):
            label += (
                "; Lively SaveData was not updated: "
                f"{persistence.get('error') or 'unknown error'}"
            )
        elif lively_count:
            label += f" (+ Lively saved for {lively_count} monitor(s))"
        self.begin_wait(
            "apply",
            label,
            wait_file=entry["file"],
            wait_name=entry["name"],
        )

    def capture_current(self):
        if self._busy:
            return

        name = self.name_var.get().strip()
        if not name:
            messagebox.showinfo("Save preset", "Enter a preset name first.")
            return

        entry = self.selected_entry()
        existing_file = entry["file"] if entry and entry["name"] == name else None
        monitor = self._selected_monitor()
        self.store.target_monitor = monitor
        self.config["targetMonitor"] = monitor
        save_config(self.config)

        self.store.write_command(
            "capture",
            monitor=monitor,
            name=name,
            file=existing_file,
        )
        self.begin_wait("capture", f"Saving '{name}' (monitor {monitor})", wait_name=name)

    def rename_selected(self):
        entry = self.selected_entry()
        if not entry:
            messagebox.showinfo("Rename", "Select a preset first.")
            return

        new_name = simpledialog.askstring(
            "Rename preset",
            "New name:",
            initialvalue=entry["name"],
        )
        if not new_name:
            return

        try:
            self.store.rename_preset(entry["file"], new_name)
            self.refresh_list(select_name=new_name, message=f"Renamed to '{new_name}'")
        except Exception as error_info:
            messagebox.showerror("Rename failed", str(error_info))

    def delete_selected(self):
        entry = self.selected_entry()
        if not entry:
            messagebox.showinfo("Delete", "Select a preset first.")
            return

        if not messagebox.askyesno("Delete preset", f"Delete '{entry['name']}'?"):
            return

        try:
            self.store.delete_preset(entry["file"])
            self.name_var.set("")
            self.refresh_list(message=f"Deleted '{entry['name']}'")
        except Exception as error_info:
            messagebox.showerror("Delete failed", str(error_info))

    def duplicate_selected(self):
        entry = self.selected_entry()
        if not entry:
            messagebox.showinfo("Duplicate", "Select a preset first.")
            return

        try:
            created = self.store.duplicate_preset(entry["file"])
            self.refresh_list(
                select_name=created["name"],
                message=f"Created '{created['name']}'",
            )
        except Exception as error_info:
            messagebox.showerror("Duplicate failed", str(error_info))

    def backup_all(self):
        try:
            target = self.store.create_backup()
            messagebox.showinfo("Backup complete", f"Saved to:\n{target}")
        except Exception as error_info:
            messagebox.showerror("Backup failed", str(error_info))

    def restore_backup(self):
        if not messagebox.askyesno(
            "Restore backup",
            "Restore the latest backup into your presets folder?",
        ):
            return

        try:
            restored = self.store.restore_latest_backup()
            if restored is None:
                messagebox.showinfo("Restore", "No backup found.")
                return
            self.refresh_list(message="Restored latest backup")
            messagebox.showinfo("Restore complete", f"Restored from:\n{restored}")
        except Exception as error_info:
            messagebox.showerror("Restore failed", str(error_info))

    def open_settings(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Settings")
        dialog.geometry("520x280")
        dialog.transient(self.root)
        dialog.grab_set()

        lively = self.store.lively_sync.path_summary()
        ttk.Label(dialog, text="Detected automatically", padding=(12, 12)).pack(anchor="w")
        ttk.Label(
            dialog,
            text=f"Installed wallpaper:\n{lively.get('installedWallpaperPath', '')}",
            wraplength=480,
            padding=(12, 0),
        ).pack(anchor="w")
        ttk.Label(
            dialog,
            text=f"SaveData:\n{lively.get('savedataDir', '')}",
            wraplength=480,
            padding=(12, 8),
        ).pack(anchor="w")

        ttk.Label(dialog, text="Override wallpaper folder (optional)", padding=(12, 0)).pack(anchor="w")
        override_var = tk.StringVar(value=self.config.get("wallpaperPathOverride", ""))
        ttk.Entry(dialog, textvariable=override_var).pack(fill="x", padx=12)

        row = ttk.Frame(dialog, padding=12)
        row.pack(fill="x")

        def browse():
            chosen = filedialog.askdirectory(
                title="Optional wallpaper override",
                initialdir=override_var.get() or str(self.store.wallpaper_path),
            )
            if chosen:
                override_var.set(chosen)

        def apply_settings():
            override = override_var.get().strip()
            if override:
                path = Path(override)
                if not path.exists():
                    messagebox.showerror("Invalid path", "Folder does not exist.", parent=dialog)
                    return
                self.config["wallpaperPathOverride"] = str(path)
            else:
                self.config.pop("wallpaperPathOverride", None)
            save_config(self.config)
            self.config = load_config()
            self.store = create_preset_store(self.config)
            self.server.stop()
            self.server = PresetApiServer(self.store, port=self.port)
            self.server.start()
            self._load_monitors()
            self.refresh_list()
            dialog.destroy()

        ttk.Button(row, text="Browse", command=browse).pack(side="left")
        ttk.Button(row, text="Save", command=apply_settings).pack(side="right")

    def poll_health(self):
        if not self._busy:
            try:
                with request.urlopen(f"{self.api_base}/api/health", timeout=1) as response:
                    json.loads(response.read().decode("utf-8"))
            except (error.URLError, TimeoutError, json.JSONDecodeError):
                self.set_status(
                    "Server running. Start the mt17 wallpaper in Lively.",
                    ok=False,
                )
        self.root.after(5000, self.poll_health)

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def on_close(self):
        self.server.stop()
        self.root.destroy()


if __name__ == "__main__":
    args = sys.argv[1:]
    force_tk = "--tk" in args
    force_web = "--web" in args

    if force_tk:
        PresetManagerApp().run()
    elif force_web:
        if not flask_available():
            print(
                "Flask is not installed. Install dependencies with: "
                "python -m pip install -r requirements.txt"
            )
            print("Starting desktop UI instead.")
            PresetManagerApp().run()
        else:
            from webui import run_webui

            run_webui(load_config())
    elif flask_available():
        from webui import run_webui

        run_webui(load_config())
    else:
        PresetManagerApp().run()
