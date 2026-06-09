import json
import os
from pathlib import Path

from lively_paths import LivelyPathResolver


APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "config.json"
BACKUP_ROOT = Path(os.path.expandvars(r"%LOCALAPPDATA%\Mt17PresetManager\backups"))


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
    else:
        config = {}

    # Migrate legacy key
    if "wallpaperPathOverride" not in config and config.get("wallpaperPath"):
        legacy = Path(config["wallpaperPath"])
        resolver_probe = LivelyPathResolver()
        try:
            auto_path = resolver_probe.installed_wallpaper_path()
            if legacy.resolve() != auto_path.resolve():
                config["wallpaperPathOverride"] = str(legacy)
        except FileNotFoundError:
            config["wallpaperPathOverride"] = str(legacy)

    override = config.get("wallpaperPathOverride")
    override_path = Path(override) if override else None
    resolver = LivelyPathResolver(override_path)

    config["wallpaperPath"] = str(resolver.installed_wallpaper_path())
    config.setdefault("apiPort", 8766)
    config.setdefault("webPort", 8767)
    config.setdefault("targetMonitor", _default_monitor(resolver))
    return config


def _default_monitor(resolver: LivelyPathResolver) -> str:
    monitors = resolver.list_monitors()
    if monitors:
        return monitors[0]["id"]
    return "1"


def save_config(config: dict) -> None:
    payload = {
        "apiPort": int(config.get("apiPort", 8766)),
        "webPort": int(config.get("webPort", 8767)),
        "targetMonitor": str(config.get("targetMonitor", "1")),
    }
    override = config.get("wallpaperPathOverride")
    if override:
        payload["wallpaperPathOverride"] = str(override)
    with CONFIG_PATH.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def create_preset_store(config: dict | None = None) -> "PresetStore":
    from preset_store import PresetStore

    config = config or load_config()
    override = config.get("wallpaperPathOverride")
    return PresetStore(
        BACKUP_ROOT,
        override_path=Path(override) if override else None,
        target_monitor=str(config.get("targetMonitor", "1")),
    )
