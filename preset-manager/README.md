# mt17 Preset Manager

Companion app for saving and applying wallpaper presets.

**Full beginner guides (wallpaper + preset manager):**

- [English](../README.md)
- [فارسی / Persian](../README.fa.md)

## Quick start

1. Double-click **`start.bat`**
2. Keep **mt17** running in Lively
3. **Save current look** or **Apply to wallpaper**

| UI | When |
|----|------|
| Web (http://127.0.0.1:8767) | Flask installed from `requirements.txt` |
| Desktop window | Flask not installed |

```bat
python main.py --web
python main.py --tk
```

See the main README for setup, troubleshooting, and all features.

**Path:** Presets and assets use the wallpaper folder that contains `preset-manager/` (auto-detected from script location).

**Portable ZIP (web UI):** Download/upload preset or full-backup ZIP files with bundled media, fonts, and images.

**Lively persistence:** Apply and Save update both the live wallpaper and Lively SaveData per monitor.
If SaveData is unavailable, the status reports a partial result: the local preset or live command may succeed, but settings will not survive a reboot until Lively and the selected monitor are available.

## Developer verification

From the repository root, run:

```bat
python -m pytest
python -m compileall preset-manager
```

These checks cover the preset manager's isolated Python behavior; they do not require or simulate a running Lively instance.
