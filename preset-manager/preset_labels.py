PRESET_GROUPS = [
    ("Visibility", [
        ("show_visualizer", "Show visualizer"),
        ("show_animated_background", "Show animated background"),
        ("show_cover", "Show album art"),
        ("show_song_name", "Show song title"),
        ("show_singer", "Show artist"),
        ("show_weather", "Show weather"),
        ("show_sys_info", "Show system info"),
        ("show_cpu", "Show CPU"),
        ("show_gpu", "Show GPU"),
        ("show_mem", "Show memory"),
        ("show_clock1", "Show clock"),
        ("showAllDays", "Show all weekdays"),
        ("show_network", "Show network speed"),
    ]),
    ("Background", [
        ("BackgroundSource", "Animated background"),
        ("BackgroundImageSource", "Static wallpaper"),
        ("backgroundColor", "Background color"),
    ]),
    ("Media", [
        ("albumArtSize", "Album art size"),
        ("titleFontSize", "Title font size"),
        ("artistFontSize", "Artist font size"),
        ("mediaTitleColor", "Title color"),
        ("mediaColor", "Artist color"),
        ("contentTop", "Media vertical position"),
        ("contentLeft", "Media horizontal position"),
        ("songNameLimit", "Song title length limit"),
    ]),
    ("Visualizer", [
        ("linesColor", "Visualizer color"),
        ("visualizerLeft", "Visualizer horizontal"),
        ("visualizerTop", "Visualizer vertical"),
        ("visualizerWidth", "Visualizer width"),
        ("visualizerHeight", "Visualizer height"),
        ("visualizerMargin", "Visualizer margin"),
        ("square", "Square visualizer"),
        ("visualizerGlow", "Visualizer glow"),
        ("clockFont", "Clock font"),
    ]),
    ("Weather", [
        ("weatherLeft", "Weather horizontal"),
        ("weatherbottom", "Weather vertical"),
        ("weatherTempColor", "Temperature color"),
        ("weatherDescriptionColor", "Description color"),
        ("weatherBackground", "Weather background"),
        ("weatherIconSize", "Weather icon size"),
        ("weatherFontSize", "Description font size"),
        ("weatherTempFontSize", "Temperature font size"),
        ("city", "City"),
        ("UseCity", "Use city name"),
        ("Lat", "Latitude"),
        ("Lon", "Longitude"),
        ("units", "Temperature units"),
        ("update_interval", "Refresh interval (seconds)"),
        ("apiKey", "OpenWeather API key"),
        ("show_weatherFeelsLike", "Show feels-like"),
        ("show_weatherHumidity", "Show humidity"),
        ("show_weatherWind", "Show wind speed"),
        ("weatherExtraColor", "Extra info color"),
        ("weatherExtraFontSize", "Extra info font size"),
    ]),
    ("Network", [
        ("networkBottom", "Vertical position"),
        ("networkRight", "Horizontal position"),
        ("networkColor", "Font color"),
        ("networkFontSize", "Font size"),
        ("networkBackground", "Background color"),
        ("networkUseMegabits", "Use Mb/s (off = MB/s)"),
    ]),
    ("System usage", [
        ("systemUsageTop", "Vertical position"),
        ("systemUsageRight", "Horizontal position"),
        ("systemUsageColor", "Text color"),
        ("systemUsageBackground", "Background color"),
        ("systemUsageFontSize", "Font size"),
        ("cpuDecimalnumber", "CPU decimals"),
        ("gpuDecimalnumber", "GPU decimals"),
        ("memDecimalnumber", "Memory decimals"),
    ]),
    ("Clock", [
        ("clock1Left", "Horizontal position (%)"),
        ("clock1Top", "Vertical position"),
        ("clock1TimeBottom", "Time vertical offset"),
        ("clock1TimeFontSize", "Time font size"),
        ("clock1TimeGap", "Time gap"),
        ("clock1AmPmFontSize", "AM/PM font size"),
        ("clock1DaysBottom", "Weekdays vertical offset"),
        ("clock1DaysGap", "Weekdays gap"),
        ("clock1DaysFontSize", "Weekdays font size"),
        ("clock1DateBottom", "Date vertical offset"),
        ("clock1DateGap", "Date gap"),
        ("clock1DateFontSize", "Date font size"),
        ("clock1TimeColor", "Time color"),
        ("clock1TodayColor", "Today color"),
        ("clock1OtherDaysColor", "Other days color"),
        ("clock1DateColor", "Date color"),
        ("clock24Hour", "24-hour format"),
    ]),
    ("Fonts", [
        ("fontFiles.mediaTitleFont", "Song title font"),
        ("fontFiles.mediaArtistFont", "Artist font"),
        ("fontFiles.weatherFont", "Weather font"),
        ("fontFiles.systemUsageFont", "System usage font (also network speed)"),
        ("fontFiles.clock1TimeFont", "Clock font"),
    ]),
]


def _get_nested_value(data: dict, key: str):
    if "." not in key:
        return data.get(key)
    head, tail = key.split(".", 1)
    nested = data.get(head)
    if not isinstance(nested, dict):
        return None
    return nested.get(tail)


def _format_value(key: str, value) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "On" if value else "Off"
    if key == "units":
        return "Imperial (°F)" if value == 1 else "Metric (°C)"
    if key == "apiKey":
        text = str(value).strip()
        if not text:
            return "(not set)"
        if len(text) <= 8:
            return "••••••••"
        return f"{text[:4]}…{text[-4:]}"
    if isinstance(value, (int, float)):
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)
    if isinstance(value, dict):
        return json_inline(value)
    return str(value)


def json_inline(value: dict) -> str:
    return ", ".join(f"{key}: {item}" for key, item in value.items())


def build_preset_view(data: dict) -> list[dict]:
    rows: list[dict] = []
    for group_name, fields in PRESET_GROUPS:
        group_rows = []
        for key, label in fields:
            value = _get_nested_value(data, key)
            if value is None and key not in data and "." not in key:
                continue
            group_rows.append(
                {
                    "key": key,
                    "label": label,
                    "value": _format_value(key, value),
                    "raw": value,
                }
            )
        if group_rows:
            rows.append({"group": group_name, "items": group_rows})

    known_keys = {key for _, fields in PRESET_GROUPS for key, _ in fields}
    known_keys.add("version")
    known_keys.add("fontFiles")

    extras = []
    for key, value in sorted(data.items()):
        if key in known_keys or key == "fontFiles":
            continue
        extras.append(
            {
                "key": key,
                "label": key,
                "value": _format_value(key, value),
                "raw": value,
            }
        )
    if extras:
        rows.append({"group": "Other", "items": extras})

    return rows
