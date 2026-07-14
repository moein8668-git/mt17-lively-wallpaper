import copy
import json
import re
from pathlib import Path


FONT_CATALOG = [
    "mediaFont.otf",
    "weatherFont.ttf",
    "systemFont.ttf",
    "clock1Font.ttf",
    "clock1DateFont.ttf",
]

DIRECT_PRESET_KEYS = {
    "show_visualizer",
    "show_animated_background",
    "show_cover",
    "show_song_name",
    "show_singer",
    "show_weather",
    "show_sys_info",
    "show_cpu",
    "show_gpu",
    "show_mem",
    "show_clock1",
    "showAllDays",
    "albumArtSize",
    "titleFontSize",
    "artistFontSize",
    "visualizerLeft",
    "visualizerTop",
    "visualizerWidth",
    "visualizerHeight",
    "visualizerMargin",
    "contentTop",
    "contentLeft",
    "songNameLimit",
    "square",
    "visualizerGlow",
    "show_weatherFeelsLike",
    "show_weatherHumidity",
    "show_weatherWind",
    "weatherExtraColor",
    "weatherExtraFontSize",
    "show_network",
    "networkBottom",
    "networkRight",
    "networkColor",
    "networkFontSize",
    "networkBackground",
    "clock24Hour",
    "cpuDecimalnumber",
    "gpuDecimalnumber",
    "memDecimalnumber",
    "weatherbottom",
    "weatherLeft",
    "weatherTempColor",
    "weatherTempFontSize",
    "weatherDescriptionColor",
    "weatherBackground",
    "weatherIconSize",
    "weatherFontSize",
    "systemUsageTop",
    "systemUsageRight",
    "systemUsageBackground",
    "systemUsageColor",
    "systemUsageFontSize",
    "mediaColor",
    "mediaTitleColor",
    "clock1TimeColor",
    "clock1TodayColor",
    "clock1OtherDaysColor",
    "clock1DateColor",
    "clock1TimeBottom",
    "clock1TimeFontSize",
    "clock1TimeGap",
    "clock1AmPmFontSize",
    "clock1DaysBottom",
    "clock1DaysGap",
    "clock1DaysFontSize",
    "clock1DateBottom",
    "clock1DateGap",
    "clock1DateFontSize",
    "clock1Left",
    "clock1Top",
    "update_interval",
}

LIVELY_KEY_ALIASES = {
    "songTitleFont": ("mediaTitleFont",),
    "songArtistFont": ("mediaArtistFont",),
}

FONT_PRESET_TO_LIVELY = {
    "mediaTitleFont": "songTitleFont",
    "mediaArtistFont": "songArtistFont",
    "weatherFont": "weatherFont",
    "systemUsageFont": "systemUsageFont",
    "clock1TimeFont": "clockFont",
    "clock1DaysFont": "clockFont",
    "clock1DateFont": "clockFont",
}


def filename_to_font_index(filename: str) -> int:
    base = basename_from_media_path(filename)
    try:
        return FONT_CATALOG.index(base)
    except ValueError:
        return 0


def basename_from_media_path(value: str) -> str:
    if not value:
        return value
    normalized = str(value).replace("\\", "/")
    return Path(normalized).name


def color_to_hex(value) -> str:
    if value is None:
        return value
    text = str(value).strip()
    if text.startswith("#"):
        return text
    match = re.match(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", text, re.I)
    if match:
        r, g, b = (int(match.group(i)) for i in range(1, 4))
        return f"#{r:02X}{g:02X}{b:02X}"
    return text


def preset_to_lively_values(preset: dict) -> dict[str, object]:
    values: dict[str, object] = {}

    for key in DIRECT_PRESET_KEYS:
        if key in preset:
            values[key] = preset[key]

    if "linesColor" in preset:
        values["lineColor"] = color_to_hex(preset["linesColor"])

    if "backgroundColor" in preset:
        values["backgroundColor"] = color_to_hex(preset["backgroundColor"])

    if "networkBackground" in preset:
        values["networkBackground"] = color_to_hex(preset["networkBackground"])

    if "networkUseMegabits" in preset:
        values["networkSpeedUnit"] = 0 if preset["networkUseMegabits"] else 1

    if "BackgroundSource" in preset:
        values["animated_background"] = basename_from_media_path(preset["BackgroundSource"])

    if "BackgroundImageSource" in preset:
        values["updateStaticWallpaper"] = basename_from_media_path(preset["BackgroundImageSource"])

    if "apiKey" in preset:
        values["OpenWeather_API"] = preset["apiKey"]

    if "city" in preset:
        values["OpenWeather_city"] = preset["city"]

    if "UseCity" in preset:
        values["OpenWeather_UseCity"] = preset["UseCity"]

    if "Lat" in preset:
        values["OpenWeather_Lat"] = str(preset["Lat"])

    if "Lon" in preset:
        values["OpenWeather_Lon"] = str(preset["Lon"])

    if "units" in preset:
        units = preset["units"]
        if isinstance(units, int):
            values["OpenWeather_units"] = units
        else:
            values["OpenWeather_units"] = 1 if str(units).lower() == "imperial" else 0

    font_files = preset.get("fontFiles") or {}
    if isinstance(font_files, dict):
        for preset_key, lively_key in FONT_PRESET_TO_LIVELY.items():
            if preset_key in font_files:
                values[lively_key] = basename_from_media_path(font_files[preset_key])

    return values


def _clamp_dropdown_index(value, items: list) -> int:
    if not items:
        return 0
    try:
        index = int(value)
    except (TypeError, ValueError):
        if isinstance(value, str) and value in items:
            return items.index(value)
        if isinstance(value, str):
            return filename_to_font_index(value)
        return 0
    return max(0, min(index, len(items) - 1))


def repair_lively_properties(saved: dict, template: dict) -> dict:
    """Restore template structure so folder/filter/items/step are never missing in SaveData."""
    repaired: dict = {}
    for key, template_entry in template.items():
        if not isinstance(template_entry, dict):
            continue

        entry = copy.deepcopy(template_entry)
        saved_entry = saved.get(key)
        if not isinstance(saved_entry, dict) or "value" not in saved_entry:
            for alias in LIVELY_KEY_ALIASES.get(key, ()):
                alias_entry = saved.get(alias)
                if isinstance(alias_entry, dict) and "value" in alias_entry:
                    saved_entry = alias_entry
                    break
        if not isinstance(saved_entry, dict) or "value" not in saved_entry:
            repaired[key] = entry
            continue

        raw_value = saved_entry["value"]
        prop_type = entry.get("type", "")

        if prop_type == "dropdown":
            items = entry.get("items") or []
            entry["value"] = _clamp_dropdown_index(raw_value, items)
        elif prop_type == "folderDropdown":
            if isinstance(raw_value, (int, float)) or (
                isinstance(raw_value, str) and str(raw_value).strip().isdigit()
            ):
                idx = int(raw_value)
                entry["value"] = FONT_CATALOG[idx] if 0 <= idx < len(FONT_CATALOG) else basename_from_media_path(
                    str(template_entry.get("value", ""))
                )
            else:
                entry["value"] = basename_from_media_path(str(raw_value))
        else:
            entry["value"] = _coerce_value(prop_type, raw_value)

        repaired[key] = entry

    return repaired


def _coerce_value(prop_type: str, value):
    if prop_type == "checkbox":
        return bool(value)
    if prop_type == "slider":
        number = float(value)
        if number.is_integer():
            return int(number) if abs(number) >= 1 else number
        return number
    if prop_type == "dropdown":
        return int(value)
    if prop_type == "textbox":
        return str(value)
    if prop_type == "color":
        return color_to_hex(value)
    if prop_type == "folderDropdown":
        return basename_from_media_path(str(value))
    return value


def merge_preset_into_lively_properties(properties: dict, preset: dict) -> dict:
    values = preset_to_lively_values(preset)
    for lively_key, new_value in values.items():
        if lively_key not in properties:
            continue
        entry = properties[lively_key]
        if not isinstance(entry, dict) or "value" not in entry:
            continue
        prop_type = entry.get("type", "")
        if prop_type == "button":
            continue
        entry["value"] = _coerce_value(prop_type, new_value)
        if prop_type == "dropdown":
            entry["value"] = _clamp_dropdown_index(entry["value"], entry.get("items") or [])
    return properties


def write_lively_properties(path: Path, properties: dict) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(properties, handle, indent=2)


def read_lively_properties(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


class LivelySettingsSync:
    def __init__(self, override_path: Path | None = None):
        from lively_paths import LivelyPathResolver

        self.resolver = LivelyPathResolver(override_path)

    def apply_preset(self, preset: dict, monitor_id: str | None = None) -> list[Path]:
        property_files = self.resolver.monitor_property_files(monitor_id)
        if not property_files:
            label = monitor_id or "selected"
            raise FileNotFoundError(
                f"No Lively SaveData found for monitor '{label}'. Is this wallpaper in Lively?"
            )

        template_path = self.resolver.local_wallpaper_path
        template = None
        if template_path:
            template_file = template_path / "LivelyProperties.json"
            if template_file.exists():
                template = read_lively_properties(template_file)

        updated: list[Path] = []
        for prop_file in property_files:
            properties = read_lively_properties(prop_file)
            if template:
                properties = repair_lively_properties(properties, template)
            merge_preset_into_lively_properties(properties, preset)
            write_lively_properties(prop_file, properties)
            updated.append(prop_file)
        return updated

    def list_monitors(self) -> list[dict]:
        return self.resolver.list_monitors()

    def path_summary(self) -> dict:
        return self.resolver.summary()
