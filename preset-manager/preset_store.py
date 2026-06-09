import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path


MANIFEST_NAME = "manifest.json"
PRESET_SUFFIX = ".preset.json"
COMMAND_FILE = "_command.json"
SLIDESHOW_FILE = "slideshow.json"
SLIDESHOW_MIN_INTERVAL = 30
SLIDESHOW_MAX_INTERVAL = 86400
SLIDESHOW_MIN_CROSSFADE = 0
SLIDESHOW_MAX_CROSSFADE = 10
SLIDESHOW_ORDERS = ("sequential", "random", "shuffle")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", name.strip()).replace(" ", "-")
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    if not cleaned:
        cleaned = "preset"
    if not cleaned.endswith(PRESET_SUFFIX):
        cleaned = f"{cleaned}{PRESET_SUFFIX}"
    return cleaned


from lively_properties import LivelySettingsSync


class PresetStore:
    def __init__(
        self,
        backup_root: Path,
        override_path: Path | None = None,
        target_monitor: str = "1",
    ):
        self.override_path = Path(override_path) if override_path else None
        self.target_monitor = str(target_monitor or "1")
        self.lively_sync = LivelySettingsSync(self.override_path)
        self.wallpaper_path = self.lively_sync.resolver.installed_wallpaper_path()
        self.presets_dir = self.wallpaper_path / "presets"
        self.manifest_path = self.presets_dir / MANIFEST_NAME
        self.backup_root = Path(backup_root)
        self.presets_dir.mkdir(parents=True, exist_ok=True)
        self.backup_root.mkdir(parents=True, exist_ok=True)
        self.slideshow_path = self.presets_dir / SLIDESHOW_FILE
        self._ensure_manifest()
        self._ensure_slideshow()

    def refresh_paths(self, override_path: Path | None = None, target_monitor: str | None = None):
        if override_path is not None:
            self.override_path = Path(override_path) if override_path else None
        if target_monitor is not None:
            self.target_monitor = str(target_monitor)
        self.lively_sync = LivelySettingsSync(self.override_path)
        self.wallpaper_path = self.lively_sync.resolver.installed_wallpaper_path()
        self.presets_dir = self.wallpaper_path / "presets"
        self.manifest_path = self.presets_dir / MANIFEST_NAME
        self.presets_dir.mkdir(parents=True, exist_ok=True)
        self.slideshow_path = self.presets_dir / SLIDESHOW_FILE
        self._ensure_manifest()
        self._ensure_slideshow()

    def _default_slideshow(self) -> dict:
        return {
            "version": 1,
            "enabled": False,
            "intervalSeconds": 300,
            "order": "sequential",
            "playlist": [],
            "pausedUntilManualResume": False,
            "crossfadeSeconds": 1.2,
        }

    def _ensure_slideshow(self) -> None:
        if not self.slideshow_path.exists():
            self._write_slideshow_file(self._default_slideshow())

    def _write_slideshow_file(self, data: dict) -> None:
        with self.slideshow_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)

    def _validate_slideshow(self, data: dict) -> dict:
        if not isinstance(data, dict):
            raise ValueError("Slideshow config must be a JSON object")

        base = self._default_slideshow()
        enabled = bool(data.get("enabled", base["enabled"]))
        paused = bool(data.get("pausedUntilManualResume", base["pausedUntilManualResume"]))

        try:
            interval = int(data.get("intervalSeconds", base["intervalSeconds"]))
        except (TypeError, ValueError) as error:
            raise ValueError("intervalSeconds must be an integer") from error
        interval = max(SLIDESHOW_MIN_INTERVAL, min(interval, SLIDESHOW_MAX_INTERVAL))

        try:
            crossfade = float(data.get("crossfadeSeconds", base["crossfadeSeconds"]))
        except (TypeError, ValueError) as error:
            raise ValueError("crossfadeSeconds must be a number") from error
        crossfade = max(
            SLIDESHOW_MIN_CROSSFADE,
            min(crossfade, SLIDESHOW_MAX_CROSSFADE),
        )

        order = str(data.get("order", base["order"])).lower()
        if order not in SLIDESHOW_ORDERS:
            raise ValueError(f"order must be one of: {', '.join(SLIDESHOW_ORDERS)}")

        raw_playlist = data.get("playlist", base["playlist"])
        if not isinstance(raw_playlist, list):
            raise ValueError("playlist must be an array of preset filenames")

        playlist: list[str] = []
        seen: set[str] = set()
        for item in raw_playlist:
            if not isinstance(item, str):
                continue
            filename = item.strip()
            if not filename.endswith(PRESET_SUFFIX):
                continue
            if filename in seen:
                continue
            if not (self.presets_dir / filename).exists():
                continue
            seen.add(filename)
            playlist.append(filename)

        if enabled and not playlist:
            enabled = False

        return {
            "version": 1,
            "enabled": enabled,
            "intervalSeconds": interval,
            "order": order,
            "playlist": playlist,
            "pausedUntilManualResume": paused,
            "crossfadeSeconds": crossfade,
        }

    def read_slideshow(self) -> dict:
        self._ensure_slideshow()
        with self.slideshow_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return self._validate_slideshow(data)

    def write_slideshow(self, data: dict) -> dict:
        validated = self._validate_slideshow(data)
        self._write_slideshow_file(validated)
        return validated

    def slideshow_with_labels(self) -> dict:
        config = self.read_slideshow()
        manifest = {entry["file"]: entry["name"] for entry in self.list_presets()}
        items = [
            {"file": filename, "name": manifest.get(filename, filename)}
            for filename in config["playlist"]
        ]
        return {**config, "playlistItems": items}

    def _ensure_manifest(self) -> None:
        if not self.manifest_path.exists():
            self._write_manifest({"version": 1, "presets": []})

    def _read_manifest(self) -> dict:
        with self.manifest_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write_manifest(self, manifest: dict) -> None:
        with self.manifest_path.open("w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2)

    def sync_manifest_with_disk(self) -> dict:
        manifest = self._read_manifest()
        known_files = {entry["file"] for entry in manifest.get("presets", [])}
        on_disk = sorted(
            path.name for path in self.presets_dir.glob(f"*{PRESET_SUFFIX}")
        )

        for filename in on_disk:
            if filename in known_files:
                continue
            stem = filename[: -len(PRESET_SUFFIX)]
            manifest.setdefault("presets", []).append(
                {
                    "id": stem.lower(),
                    "name": stem.replace("-", " "),
                    "file": filename,
                    "updated": utc_now_iso(),
                }
            )

        manifest["presets"] = [
            entry
            for entry in manifest.get("presets", [])
            if (self.presets_dir / entry["file"]).exists()
        ]
        self._write_manifest(manifest)
        return manifest

    def list_presets(self) -> list[dict]:
        manifest = self.sync_manifest_with_disk()
        return sorted(manifest.get("presets", []), key=lambda item: item["name"].lower())

    def read_preset(self, filename: str) -> dict:
        path = self.presets_dir / filename
        if not path.exists():
            raise FileNotFoundError(filename)
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def save_preset(self, name: str, data: dict, filename: str | None = None) -> dict:
        manifest = self.sync_manifest_with_disk()
        filename = filename or sanitize_filename(name)
        path = self.presets_dir / filename

        with path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)

        entry = next(
            (item for item in manifest["presets"] if item["file"] == filename),
            None,
        )
        if entry is None:
            entry = {
                "id": filename[: -len(PRESET_SUFFIX)].lower(),
                "name": name.strip() or filename[: -len(PRESET_SUFFIX)],
                "file": filename,
            }
            manifest["presets"].append(entry)
        else:
            entry["name"] = name.strip() or entry["name"]

        entry["updated"] = utc_now_iso()
        self._write_manifest(manifest)
        lively_saved = self._sync_lively_savedata(data, self.target_monitor)
        if lively_saved:
            entry["livelySavedataFiles"] = lively_saved
            entry["livelyMonitor"] = self.target_monitor
        self.create_backup()
        return entry

    def _sync_lively_savedata(self, preset_data: dict, monitor_id: str | None = None) -> list[str]:
        monitor = monitor_id or self.target_monitor
        try:
            updated = self.lively_sync.apply_preset(preset_data, monitor)
            return [str(path) for path in updated]
        except FileNotFoundError:
            return []

    def list_monitors(self) -> list[dict]:
        return self.lively_sync.list_monitors()

    def rename_preset(self, filename: str, new_name: str) -> dict:
        manifest = self.sync_manifest_with_disk()
        entry = next(
            (item for item in manifest["presets"] if item["file"] == filename),
            None,
        )
        if entry is None:
            raise FileNotFoundError(filename)

        new_filename = sanitize_filename(new_name)
        old_path = self.presets_dir / filename
        new_path = self.presets_dir / new_filename
        if old_path.exists() and old_path != new_path:
            if new_path.exists():
                raise FileExistsError(new_filename)
            old_path.rename(new_path)

        entry["name"] = new_name.strip()
        entry["file"] = new_filename
        entry["id"] = new_filename[: -len(PRESET_SUFFIX)].lower()
        entry["updated"] = utc_now_iso()
        self._write_manifest(manifest)
        self._sync_slideshow_preset_rename(filename, new_filename)
        self.create_backup()
        return entry

    def _sync_slideshow_preset_rename(self, old_file: str, new_file: str) -> None:
        if not self.slideshow_path.exists():
            return
        try:
            config = self.read_slideshow()
        except (json.JSONDecodeError, ValueError):
            return
        playlist = config.get("playlist", [])
        if old_file not in playlist:
            return
        config["playlist"] = [
            new_file if item == old_file else item for item in playlist
        ]
        self.write_slideshow(config)

    def _sync_slideshow_preset_remove(self, filename: str) -> None:
        if not self.slideshow_path.exists():
            return
        try:
            config = self.read_slideshow()
        except (json.JSONDecodeError, ValueError):
            return
        playlist = [item for item in config.get("playlist", []) if item != filename]
        config["playlist"] = playlist
        if not playlist:
            config["enabled"] = False
        self.write_slideshow(config)

    def delete_preset(self, filename: str) -> None:
        manifest = self.sync_manifest_with_disk()
        path = self.presets_dir / filename
        if path.exists():
            path.unlink()

        manifest["presets"] = [
            item for item in manifest["presets"] if item["file"] != filename
        ]
        self._write_manifest(manifest)
        self._sync_slideshow_preset_remove(filename)
        self.create_backup()

    def duplicate_preset(self, filename: str) -> dict:
        data = self.read_preset(filename)
        manifest = self.sync_manifest_with_disk()
        source = next(
            (item for item in manifest["presets"] if item["file"] == filename),
            None,
        )
        base_name = source["name"] if source else filename[: -len(PRESET_SUFFIX)]
        copy_name = f"{base_name} Copy"
        return self.save_preset(copy_name, data)

    def import_preset(self, source_file: Path, name: str | None = None) -> dict:
        with Path(source_file).open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        preset_name = name or Path(source_file).stem.replace("-", " ")
        return self.save_preset(preset_name, data)

    def import_preset_data(self, data: dict, name: str | None = None) -> dict:
        if not isinstance(data, dict):
            raise ValueError("Preset data must be a JSON object")
        preset_name = (name or "Imported Preset").strip() or "Imported Preset"
        return self.save_preset(preset_name, data)

    def export_preset(self, filename: str, destination: Path) -> None:
        data = self.read_preset(filename)
        with Path(destination).open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)

    def create_backup(self) -> Path:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target = self.backup_root / stamp
        target.mkdir(parents=True, exist_ok=True)
        if self.presets_dir.exists():
            shutil.copytree(
                self.presets_dir,
                target / "presets",
                dirs_exist_ok=True,
            )
        backups = sorted(self.backup_root.glob("*"), reverse=True)
        for old in backups[20:]:
            shutil.rmtree(old, ignore_errors=True)
        return target

    def restore_latest_backup(self) -> Path | None:
        backups = sorted(self.backup_root.glob("*"), reverse=True)
        if not backups:
            return None

        latest = backups[0]
        source = latest / "presets"
        if not source.exists():
            return None

        if self.presets_dir.exists():
            shutil.rmtree(self.presets_dir)
        shutil.copytree(source, self.presets_dir)
        self.sync_manifest_with_disk()
        return latest

    def build_backup_bundle(self) -> dict:
        manifest = self.sync_manifest_with_disk()
        presets = {}
        for entry in manifest.get("presets", []):
            presets[entry["file"]] = self.read_preset(entry["file"])
        return {
            "version": 1,
            "exportedAt": utc_now_iso(),
            "manifest": manifest,
            "presets": presets,
        }

    def restore_backup_bundle(self, bundle: dict) -> int:
        if not isinstance(bundle, dict):
            raise ValueError("Invalid backup file")

        manifest = bundle.get("manifest")
        presets = bundle.get("presets")
        if not isinstance(manifest, dict) or not isinstance(presets, dict):
            raise ValueError("Backup must include manifest and presets")

        self.presets_dir.mkdir(parents=True, exist_ok=True)
        for path in self.presets_dir.iterdir():
            if path.name in (COMMAND_FILE, SLIDESHOW_FILE):
                continue
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)

        saved_count = 0
        for filename, data in presets.items():
            if not isinstance(filename, str) or not filename.endswith(PRESET_SUFFIX):
                continue
            if not isinstance(data, dict):
                continue
            with (self.presets_dir / filename).open("w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2)
            saved_count += 1

        self._write_manifest(manifest)
        self.sync_manifest_with_disk()
        self.create_backup()
        return saved_count

    def write_command(self, action: str, monitor: str | None = None, **payload) -> dict:
        monitor_id = str(monitor or self.target_monitor)
        lively_saved: list[str] = []
        if action == "apply" and payload.get("file"):
            preset_data = self.read_preset(payload["file"])
            lively_saved = self._sync_lively_savedata(preset_data, monitor_id)
            self._pause_slideshow_for_manual_apply()
        elif action == "capture":
            pass

        command = {"action": action, "monitor": monitor_id, **payload}
        with (self.presets_dir / COMMAND_FILE).open("w", encoding="utf-8") as handle:
            json.dump(command, handle)
        return {"livelySavedataFiles": lively_saved, "monitor": monitor_id}

    def clear_command(self) -> None:
        path = self.presets_dir / COMMAND_FILE
        if path.exists():
            path.unlink()

    def _pause_slideshow_for_manual_apply(self) -> None:
        if not self.slideshow_path.exists():
            return
        try:
            config = self.read_slideshow()
        except (json.JSONDecodeError, ValueError):
            return
        if not config.get("enabled"):
            return
        config["pausedUntilManualResume"] = True
        self.write_slideshow(config)
