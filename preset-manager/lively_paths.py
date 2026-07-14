import json
import os
from pathlib import Path


PRESET_MANAGER_DIR = Path(__file__).resolve().parent


def wallpaper_folder_from_script() -> Path:
    """
    Wallpaper root is always the folder that contains preset-manager.
    Works no matter where the user cloned or copied the project.
    """
    parent = PRESET_MANAGER_DIR.parent
    info_path = parent / "LivelyInfo.json"
    if not info_path.exists():
        raise FileNotFoundError(
            "preset-manager must live inside the mt17 wallpaper folder. "
            f"Expected LivelyInfo.json next to preset-manager, looked in: {parent}"
        )
    return parent.resolve()


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


def find_savedata_by_title(title: str) -> Path | None:
    """Find Lively SaveData wpdata folder for a wallpaper title."""
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


class LivelyPathResolver:
    """Resolve paths from preset-manager script location + Lively SaveData."""

    def __init__(self, override_path: Path | None = None):
        self.local_wallpaper_path = wallpaper_folder_from_script()
        self.override_path = Path(override_path).resolve() if override_path else None

    def wallpaper_path(self) -> Path:
        """
        Folder used for presets, assets, and wallpaper commands.
        Defaults to the parent of preset-manager (script location).
        """
        if self.override_path and self.override_path.exists():
            return self.override_path
        return self.local_wallpaper_path

    # Backward-compatible alias used across the app.
    def installed_wallpaper_path(self) -> Path:
        return self.wallpaper_path()

    def source_title(self) -> str | None:
        return read_lively_title(self.wallpaper_path())

    def library_root(self) -> Path | None:
        wallpaper = self.wallpaper_path()
        if is_library_wallpaper(wallpaper):
            return wallpaper.parent.parent.resolve()
        return lively_library_roots()[0] if lively_library_roots() else None

    def savedata_wpdata_dir(self) -> Path | None:
        wallpaper = self.wallpaper_path()

        if is_library_wallpaper(wallpaper):
            return wallpaper.parent.parent / "SaveData" / "wpdata" / wallpaper.name

        title = read_lively_title(self.local_wallpaper_path)
        if title:
            found = find_savedata_by_title(title)
            if found:
                return found

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
        wallpaper = self.wallpaper_path()
        savedata = self.savedata_wpdata_dir()
        monitors = self.list_monitors()
        using_override = (
            self.override_path is not None
            and self.override_path.resolve() == wallpaper.resolve()
        )
        return {
            "scriptWallpaperPath": str(self.local_wallpaper_path),
            "overridePath": str(self.override_path) if self.override_path else None,
            "installedWallpaperPath": str(wallpaper),
            "pathSource": "override" if using_override else "script",
            "wallpaperId": wallpaper.name,
            "savedataDir": str(savedata) if savedata else None,
            "monitors": monitors,
            "monitorPropertyFiles": [item["propertyFile"] for item in monitors],
            "title": self.source_title(),
            "autoDetected": not using_override,
        }
