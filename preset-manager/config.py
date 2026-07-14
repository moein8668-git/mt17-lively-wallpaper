import json
import os
from pathlib import Path

from lively_paths import LivelyPathResolver


APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "config.json"
BACKUP_ROOT = Path(os.path.expandvars(r"%LOCALAPPDATA%\Mt17PresetManager\backups"))
DEFAULT_API_PORT = 8766
API_PORT_RUNTIME_FILE = "_preset-api.json"


def normalize_port(value, default: int = DEFAULT_API_PORT) -> int:
    try:
        port = int(value)
    except (TypeError, ValueError):
        return default
    return port if 1 <= port <= 65535 else default


def write_api_port_runtime(wallpaper_path: Path, api_port: int) -> Path:
    runtime_path = Path(wallpaper_path) / "presets" / API_PORT_RUNTIME_FILE
    runtime_path.parent.mkdir(parents=True, exist_ok=True)
    with runtime_path.open("w", encoding="utf-8") as handle:
        json.dump({"apiPort": normalize_port(api_port)}, handle)
    return runtime_path


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
    else:
        config = {}

    # Legacy key from older builds — no longer used for auto-detection.
    config.pop("wallpaperPath", None)

    override = str(config.get("wallpaperPathOverride", "")).strip() or None
    override_path = Path(override) if override else None
    resolver = LivelyPathResolver(override_path)

    config["wallpaperPath"] = str(resolver.wallpaper_path())
    config["apiPort"] = normalize_port(config.get("apiPort", DEFAULT_API_PORT))
    config.setdefault("webPort", 8767)
    config.setdefault("targetMonitor", _default_monitor(resolver))
    write_api_port_runtime(resolver.wallpaper_path(), config["apiPort"])
    return config


def _default_monitor(resolver: LivelyPathResolver) -> str:
    monitors = resolver.list_monitors()
    if monitors:
        return monitors[0]["id"]
    return "1"


def save_config(config: dict) -> None:
    payload = {
        "apiPort": normalize_port(config.get("apiPort", DEFAULT_API_PORT)),
        "webPort": normalize_port(config.get("webPort", 8767)),
        "targetMonitor": str(config.get("targetMonitor", "1")),
    }
    override = config.get("wallpaperPathOverride")
    if override:
        payload["wallpaperPathOverride"] = str(override)
    with CONFIG_PATH.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    override = payload.get("wallpaperPathOverride")
    resolver = LivelyPathResolver(Path(override) if override else None)
    write_api_port_runtime(resolver.wallpaper_path(), payload["apiPort"])


def create_preset_store(config: dict | None = None) -> "PresetStore":
    from preset_store import PresetStore

    config = config or load_config()
    override = config.get("wallpaperPathOverride")
    return PresetStore(
        BACKUP_ROOT,
        override_path=Path(override) if override else None,
        target_monitor=str(config.get("targetMonitor", "1")),
    )
