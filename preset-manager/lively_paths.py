import json
import os
from pathlib import Path


PRESET_MANAGER_DIR = Path(__file__).resolve().parent


def lively_library_roots() -> list[Path]:
    roots: list[Path] = []
    candidates = [
        Path(
            os.path.expandvars(
                r"%LOCALAPPDATA%\Packages\12030rocksdanister.LivelyWallpaper_97hta09mmv6hy"
                r"\LocalCache\Local\Lively Wallpaper\Library"
            )
        ),
        Path(os.path.expandvars(r"%LOCALAPPDATA%\Lively Wallpaper\Library")),
    ]
    seen: set[str] = set()
    for path in candidates:
        if not path.exists():
            continue
        resolved = path.resolve()
        key = str(resolved)
        if key not in seen:
            seen.add(key)
            roots.append(resolved)
    return roots


def read_lively_title(wallpaper_path: Path) -> str | None:
    info_path = wallpaper_path / "LivelyInfo.json"
    if not info_path.exists():
        return None
    with info_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    title = data.get("Title")
    return str(title).strip() if title else None


def is_library_wallpaper(path: Path) -> bool:
    try:
        return path.parent.name == "wallpapers" and path.parent.parent.name == "Library"
    except (IndexError, AttributeError):
        return False


def find_installed_wallpaper_by_title(title: str) -> Path | None:
    for library_root in lively_library_roots():
        wallpapers_dir = library_root / "wallpapers"
        if not wallpapers_dir.exists():
            continue
        for folder in wallpapers_dir.iterdir():
            if folder.is_dir() and read_lively_title(folder) == title:
                return folder.resolve()
    return None


class LivelyPathResolver:
    """Auto-detect installed wallpaper + SaveData from preset-manager parent folder."""

    def __init__(self, override_path: Path | None = None):
        self.dev_wallpaper_path = self._detect_dev_wallpaper()
        self.override_path = Path(override_path).resolve() if override_path else None

    @staticmethod
    def _detect_dev_wallpaper() -> Path | None:
        parent = PRESET_MANAGER_DIR.parent
        if (parent / "LivelyInfo.json").exists() and (parent / "index.html").exists():
            return parent.resolve()
        return None

    def source_title(self) -> str | None:
        if self.dev_wallpaper_path:
            title = read_lively_title(self.dev_wallpaper_path)
            if title:
                return title
        if self.override_path:
            return read_lively_title(self.override_path)
        return None

    def installed_wallpaper_path(self) -> Path:
        title = self.source_title()
        if title:
            found = find_installed_wallpaper_by_title(title)
            if found:
                return found

        if self.override_path and self.override_path.exists():
            if is_library_wallpaper(self.override_path):
                return self.override_path
            if title:
                found = find_installed_wallpaper_by_title(title)
                if found:
                    return found
            return self.override_path

        if self.dev_wallpaper_path and self.dev_wallpaper_path.exists():
            return self.dev_wallpaper_path

        for library_root in lively_library_roots():
            wallpapers_dir = library_root / "wallpapers"
            if wallpapers_dir.exists():
                for folder in wallpapers_dir.iterdir():
                    if folder.is_dir() and (folder / "LivelyInfo.json").exists():
                        return folder.resolve()

        raise FileNotFoundError(
            "Could not find wallpaper in Lively. Add mt17 to Lively first."
        )

    def library_root(self) -> Path | None:
        installed = self.installed_wallpaper_path()
        if is_library_wallpaper(installed):
            return installed.parent.parent.resolve()
        return lively_library_roots()[0] if lively_library_roots() else None

    def savedata_wpdata_dir(self) -> Path | None:
        installed = self.installed_wallpaper_path()
        if is_library_wallpaper(installed):
            return installed.parent.parent / "SaveData" / "wpdata" / installed.name

        title = self.source_title()
        if not title:
            return None

        for library_root in lively_library_roots():
            wpdata_root = library_root / "SaveData" / "wpdata"
            wallpapers_dir = library_root / "wallpapers"
            if not wpdata_root.exists():
                continue
            for folder in wpdata_root.iterdir():
                if not folder.is_dir():
                    continue
                wallpaper_candidate = wallpapers_dir / folder.name
                if wallpaper_candidate.exists() and read_lively_title(wallpaper_candidate) == title:
                    return folder.resolve()
        return None

    def list_monitors(self) -> list[dict]:
        wpdata = self.savedata_wpdata_dir()
        if wpdata is None or not wpdata.exists():
            return []

        monitors: list[dict] = []
        for monitor_dir in sorted(wpdata.iterdir(), key=lambda item: item.name):
            if not monitor_dir.is_dir():
                continue
            prop_file = monitor_dir / "LivelyProperties.json"
            if not prop_file.exists():
                continue
            monitors.append(
                {
                    "id": monitor_dir.name,
                    "label": f"Monitor {monitor_dir.name}",
                    "propertyFile": str(prop_file),
                }
            )
        return monitors

    def monitor_property_file(self, monitor_id: str) -> Path | None:
        wpdata = self.savedata_wpdata_dir()
        if wpdata is None:
            return None
        prop_file = wpdata / monitor_id / "LivelyProperties.json"
        return prop_file if prop_file.exists() else None

    def monitor_property_files(self, monitor_id: str | None = None) -> list[Path]:
        if monitor_id and monitor_id != "all":
            prop_file = self.monitor_property_file(monitor_id)
            return [prop_file] if prop_file else []

        wpdata = self.savedata_wpdata_dir()
        if wpdata is None or not wpdata.exists():
            return []

        files: list[Path] = []
        for monitor_dir in sorted(wpdata.iterdir(), key=lambda item: item.name):
            if not monitor_dir.is_dir():
                continue
            prop_file = monitor_dir / "LivelyProperties.json"
            if prop_file.exists():
                files.append(prop_file)
        return files

    def summary(self) -> dict:
        installed = self.installed_wallpaper_path()
        savedata = self.savedata_wpdata_dir()
        monitors = self.list_monitors()
        return {
            "devWallpaperPath": str(self.dev_wallpaper_path) if self.dev_wallpaper_path else None,
            "overridePath": str(self.override_path) if self.override_path else None,
            "installedWallpaperPath": str(installed),
            "wallpaperId": installed.name,
            "savedataDir": str(savedata) if savedata else None,
            "monitors": monitors,
            "monitorPropertyFiles": [item["propertyFile"] for item in monitors],
            "title": self.source_title(),
            "autoDetected": True,
        }
