from lively_properties import preset_to_lively_values


def test_preset_to_lively_values_converts_representative_settings():
    preset = {
        "show_clock1": True,
        "linesColor": "rgba(12, 34, 56, 0.5)",
        "backgroundColor": "#abcdef",
        "networkUseMegabits": False,
        "BackgroundSource": r"C:\wallpaper\media\ocean.webm",
        "BackgroundImageSource": "/wallpaper/images/ocean.png",
        "apiKey": "secret",
        "city": "Tehran",
        "UseCity": True,
        "Lat": 35.7,
        "Lon": 51.4,
        "units": "imperial",
        "fontFiles": {
            "mediaTitleFont": "fonts/title.ttf",
            "clock1DateFont": "fonts/date.otf",
        },
    }

    values = preset_to_lively_values(preset)

    assert values["show_clock1"] is True
    assert values["lineColor"] == "#0C2238"
    assert values["backgroundColor"] == "#abcdef"
    assert values["networkSpeedUnit"] == 1
    assert values["animated_background"] == "ocean.webm"
    assert values["updateStaticWallpaper"] == "ocean.png"
    assert values["OpenWeather_API"] == "secret"
    assert values["OpenWeather_city"] == "Tehran"
    assert values["OpenWeather_UseCity"] is True
    assert values["OpenWeather_Lat"] == "35.7"
    assert values["OpenWeather_Lon"] == "51.4"
    assert values["OpenWeather_units"] == 1
    assert values["songTitleFont"] == "title.ttf"
    assert values["clockFont"] == "date.otf"
