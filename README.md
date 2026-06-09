# mt17 — Lively Wallpaper (complete guide)

**English** | [فارسی (Persian)](README.fa.md)

A live desktop wallpaper for [Lively Wallpaper](https://github.com/rocksdanister/lively) with music-reactive visualizer, now-playing info, weather, clock, system stats, network speed, and a **Preset Manager** companion app for saving themes and running an automatic **preset slideshow**.

---

## About this project

**mt17** is a custom HTML/JS wallpaper tuned for Lively’s WebView2 engine. It uses Lively’s built-in hooks for audio, system info, now-playing metadata, and pause events.

This project was **vibe-coded with [ChatGPT](https://chat.openai.com) and [Cursor](https://cursor.com)** — iteratively designed, debugged, and extended in AI-assisted sessions. Expect rough edges; report issues if something breaks on your setup.

**You do not need Python** to use the wallpaper itself. Python is only for the optional Preset Manager.

---

## What’s on your desktop

| Feature | Description |
|---------|-------------|
| **Animated background** | Looping video from `media/` (optional) |
| **Static background** | Image from `images/` under the video |
| **Music visualizer** | Audio-reactive wave (smooth or square), optional glow |
| **Now playing** | Title, artist, album art from Windows media session |
| **Weather** | OpenWeather — temp, description, optional feels-like / humidity / wind |
| **Clock** | Time, weekday row, date — 12h or 24h |
| **System usage** | CPU, RAM, GPU percentages |
| **Network speed** | Download / upload (Mb/s or MB/s), bottom-right |
| **Preset slideshow** | Auto-rotate saved presets with cross-fade (configured in Preset Manager **web UI**) |

When Lively **pauses** the wallpaper (battery saver / focus mode), the animated background and clock updates slow down; the visualizer skips heavy work until playback resumes.

---

## What you need

| Item | Required for | Details |
|------|----------------|---------|
| **Windows 10/11** | Wallpaper | |
| **Lively Wallpaper** | Wallpaper | [Microsoft Store](https://apps.microsoft.com/store/detail/lively-wallpaper/9ntm2qc6rlws) or [GitHub releases](https://github.com/rocksdanister/lively/releases) |
| **OpenWeather API key** | Weather only | Free key at [openweathermap.org/api](https://openweathermap.org/api) — enter in Lively Customize |
| **Python 3.10+** | Preset Manager only | [python.org](https://www.python.org/downloads/) — enable **Add Python to PATH** |
| **Flask** | Web UI (recommended) | `pip install flask` |

---

## Part 1 — Install the wallpaper in Lively

### 1. Get the wallpaper folder

You need the full project folder (title **mt17** in `LivelyInfo.json`). It must include at least:

- `index.html`, `LivelyInfo.json`, `LivelyProperties.json`
- `js/`, `styles/`, `media/`, `images/`, `fonts/`, `presets/`, `res/` (and optional `preset-manager/`)

You can develop from any folder (e.g. `D:\Live background\`) or copy into Lively’s library.

### 2. Add to Lively

**Method A — Add from Lively (recommended)**

1. Open **Lively Wallpaper**.
2. **+** → **Add wallpaper** / **Local file**.
3. Select the **folder** that contains `LivelyInfo.json` (not `index.html` alone).
4. Set **mt17** as wallpaper on your monitor(s).

**Method B — Copy into Lively library**

Copy the whole folder to:

```text
%LOCALAPPDATA%\Packages\12030rocksdanister.LivelyWallpaper_97hta09mmv6hy\LocalCache\Local\Lively Wallpaper\Library\wallpapers\
```

Lively assigns a random subfolder name (but you can choose one yourself e.g. `mt17cus2igg`). Restart Lively or refresh the library, then apply **mt17**.

### 3. Confirm it works

You should see background + widgets. Play music to test the visualizer. Right-click the wallpaper in Lively → **Customize** to tune settings.

### 4. Dev folder vs installed copy

If you edit files in a **dev folder** but Lively runs a **copy** under `Library\wallpapers\...`, changes won’t show until you copy updated files into the installed folder or re-add the dev folder in Lively.

Lively **Customize** reads settings from **SaveData**, not always from the wallpaper root file:

```text
Library\SaveData\wpdata\{wallpaper-id}\{monitor}\LivelyProperties.json
```

After updating `LivelyProperties.json` in the project, click **Reload settings from LivelyProperties.json** at the bottom of Customize (or re-add the wallpaper).

---

## Part 2 — Lively Customize (full reference)

Open **Customize** for **mt17** in Lively. All controls live in `LivelyProperties.json`.

### Fonts (top of Customize)

Five **folder dropdowns** (browse the `fonts/` folder):

| Control | Used for |
|---------|----------|
| Song title font | Now-playing title |
| Artist name font | Now-playing artist |
| Weather font | Weather panel |
| System usage font | CPU/RAM/GPU **and** network speed |
| Clock font | Time, weekdays, date |

Drop `.ttf`, `.otf`, or `.woff` files into `fonts/` and pick them in Customize or choose one in the Lively Customize panel.

### Background

| Control | Purpose |
|---------|---------|
| Animated background | Video from `media/` |
| Static wallpaper | Image from `images/` |
| Show animated background | Toggle video layer |

### Media & visualizer

| Control | Purpose |
|---------|---------|
| Show album art / song title / artist | Now-playing block |
| Album art size, title/artist font sizes & colors | Media styling |
| Media block position | `contentTop` / `contentLeft` |
| Song title character limit | Truncate long titles |
| Visualizer color, size, position, margin | Wave appearance |
| Square wave / Visualizer glow | Wave shape & glow |
| Visualizer fill color | Area under the wave |

### Weather

| Control | Purpose |
|---------|---------|
| OpenWeather API key, city or lat/lon, units | Data source |
| Refresh interval | How often to fetch |
| Position, colors, icon size | Layout & style |
| Feels-like / humidity / wind | Optional extra line |

If the API key is missing or the request fails, the weather panel shows an error message instead of breaking silently.

### System usage & network

| Control | Purpose |
|---------|---------|
| Show CPU / GPU / RAM | Individual toggles |
| System panel position, colors, font, decimals | Styling |
| Show network speed | Bottom-right ↓/↑ speeds |
| Network position, colors, background, font size | Styling |
| Network speed unit | **Mb/s** (megabit) or **MB/s** (megabyte) |

### Clock

| Control | Purpose |
|---------|---------|
| Show clock / show all weekdays | Visibility |
| 24-hour clock | Off = 12-hour with AM/PM |
| Colors, positions, font sizes, gaps | Full layout control |

### Tips

- **Presets are not in Customize** — too many controls caused crashes; use Preset Manager instead.
- **Manual Apply from Preset Manager** writes to SaveData and is the reliable way to lock a look across reboots.
- **Slideshow** does *not* write SaveData on each slide — see Part 4.

---

## Part 3 — Preset Manager

The Preset Manager is a small **Python companion app** that:

- **Saves** the current live wallpaper look as a `.preset.json` file
- **Applies** a saved preset to the running wallpaper
- **Writes Lively SaveData** on Apply/Save so settings survive reboot (per monitor)
- **Runs preset slideshow** configuration (web UI only)

Presets are stored here:

```text
{wallpaper folder}/presets/*.preset.json
{wallpaper folder}/presets/manifest.json
{wallpaper folder}/presets/slideshow.json
```

### Start the app

1. Open `preset-manager/` inside the wallpaper folder.
2. Double-click **`start.bat`**.

| If Flask is installed | If Flask is **not** installed |
|----------------------|-------------------------------|
| Browser opens **Web UI** at http://127.0.0.1:8767 | **Desktop window (Tk)** |

Install Flask (recommended):

```bat
pip install flask
```

Force a UI:

```bat
python main.py --web
python main.py --tk
```

### First-time setup

1. Keep **mt17 running** in Lively.
2. In Preset Manager **Settings** (web: top-right; Tk: Settings button):
   - **Wallpaper folder** — usually auto-detected if `preset-manager` sits inside the mt17 project. Override if needed, e.g. `...\Library\wallpapers\mt17cus2igg`.
   - **Monitor** — which monitor’s SaveData to update (web UI: dropdown on main page).
3. Save → stored in `preset-manager/config.json`.

Apply/Save needs the wallpaper **live** in Lively. The app talks to it via `presets/_command.json` (polled ~every 1.5s) and HTTP API on port **8766**.

---

## Part 4 — Using presets

### Basic workflow

1. Tune the look in **Lively Customize** (optional).
2. In Preset Manager, enter a **preset name**.
3. Click **Save current look** — waits for the wallpaper to capture state (a few seconds).
4. Later: select preset → **Apply to wallpaper**.

Apply updates the desktop immediately **and** writes matching values to Lively SaveData for the selected monitor.

### Preset slideshow (web UI only)

Rotate presets like a Windows background slideshow:

1. Create **2+ presets**.
2. In the web UI **Slideshow** section:
   - **Add selected preset** to build the playlist (use **Up/Down** to reorder).
   - Set **Interval** (minutes; minimum 30 seconds).
   - Set **Cross-fade** (seconds; `0` = instant, default `1.2`).
   - Choose **Order**: sequential, random, or shuffle (no repeat until all played).
   - Check **Enable preset slideshow**.
3. Click **Save slideshow**.

| Topic | Behavior |
|-------|----------|
| Who runs the timer | The **wallpaper** reads `presets/slideshow.json` |
| Preset Manager must stay open? | **No** — only needed to edit slideshow settings |
| SaveData on each slide | **No** — visual only; last slide stays until you manual-Apply a fixed preset |
| After reboot | Resumes if `enabled: true` in `slideshow.json` |
| Manual Apply | Pauses slideshow; save slideshow again with **Enable** checked to resume |
| Cross-fade | Dual-layer background dissolve + UI fade (slideshow only; manual Apply is instant) |

### Web UI vs Tk desktop — feature comparison

| Feature | Web UI (Flask) | Tk desktop (`--tk`) |
|---------|:--------------:|:-------------------:|
| Apply preset | Yes | Yes |
| Save current look | Yes | Yes |
| Rename / Delete / Duplicate | Yes | Yes |
| Local backup / restore latest | Yes | Yes |
| Monitor selection | Yes (main page) | Yes (Settings) |
| Wallpaper path override | Yes | Yes |
| **Preset slideshow** | **Yes** | **No** |
| **Cross-fade settings** | **Yes** | **No** |
| **View settings** (readable preset breakdown) | **Yes** | **No** |
| **Download / upload single preset JSON** | **Yes** | **No** |
| **Download / upload full backup JSON** | **Yes** | **No** |
| Wallpaper thumbnail in header | Yes | No |

**Recommendation:** Install Flask and use the **web UI** for the full experience. Tk is a minimal fallback when Flask isn’t available.

### All Preset Manager actions (web UI)

| Action | What it does |
|--------|----------------|
| **Apply to wallpaper** | Load preset + update SaveData |
| **Save current look** | Capture live state + update SaveData |
| **Rename / Delete / Duplicate** | Manage preset files |
| **View settings** | Human-readable list of saved values |
| **Download preset JSON** | Export one preset file |
| **Upload preset JSON** | Import one preset file |
| **Create local backup** | Copy `presets/` to `%LocalAppData%\Mt17PresetManager\backups\` |
| **Download backup JSON** | Export all presets + manifest in one file |
| **Upload backup JSON** | Restore from that file |
| **Restore latest local backup** | Restore most recent backup folder |
| **Save slideshow** | Write `slideshow.json` |

### Where files are stored

| What | Location |
|------|----------|
| Presets | `{wallpaper folder}/presets/*.preset.json` |
| Slideshow config | `{wallpaper folder}/presets/slideshow.json` |
| Command bridge | `{wallpaper folder}/presets/_command.json` (temporary) |
| Local backups | `%LocalAppData%\Mt17PresetManager\backups\` |
| App settings | `preset-manager/config.json` |
| Lively SaveData (per monitor) | `%LocalAppData%\...\Lively Wallpaper\Library\SaveData\wpdata\{id}\{monitor}\LivelyProperties.json` |

---

## Part 5 — Project layout

```text
mt17/
├── README.md / README.fa.md   ← Guides (English / Persian)
├── index.html                 ← Wallpaper entry
├── LivelyInfo.json            ← Lively metadata & CLI args
├── LivelyProperties.json      ← Customize panel template
├── js/
│   └── script.js              ← Wallpaper logic + slideshow timer
├── styles/
│   └── style.css
├── media/                     ← Background videos (.webm, .mp4, …)
├── images/                    ← Static wallpapers
├── fonts/                     ← Custom fonts for Customize pickers
├── res/                       ← Default album art, etc.
├── presets/
│   ├── manifest.json          ← Preset index
│   ├── slideshow.json         ← Slideshow config (web UI)
│   ├── _command.json          ← Runtime bridge (created by Preset Manager)
│   └── *.preset.json          ← Saved themes
└── preset-manager/
    ├── start.bat              ← Start Preset Manager
    ├── main.py                ← Web or Tk launcher
    ├── webui.py               ← Flask web UI (port 8767)
    ├── server.py              ← HTTP API (port 8766)
    ├── preset_store.py        ← Presets + slideshow on disk
    ├── lively_properties.py   ← SaveData sync mapping
    ├── lively_paths.py        ← Lively library / SaveData path helpers
    ├── preset_labels.py       ← Human-readable labels for View settings
    ├── config.py              ← App defaults & backup root path
    ├── requirements.txt       ← Python deps (Flask)
    ├── README.md              ← Short pointer to main guide
    ├── config.json            ← Your paths & monitor (created on save)
    ├── templates/
    │   └── index.html         ← Web UI page
    └── static/
        ├── app.js             ← Web UI logic
        └── app.css            ← Web UI styles
```

### Lively arguments (in `LivelyInfo.json`)

```text
--system-nowplaying --audio --system-information --pause-event true
```

These enable now-playing metadata, audio visualizer data, CPU/GPU/RAM/network stats, and pause notifications.

---

## Troubleshooting

### Wallpaper doesn’t appear in Lively

- Select the **folder** with `LivelyInfo.json`, not a single file.
- Restart Lively after manual copy.

### Customize is empty, crashes, or font picker opens wrong folder

- Click **Reload settings from LivelyProperties.json** in Customize.
- Font pickers are at the **top** of Customize; keep `folder: "fonts"` in SaveData (reload fixes corrupted entries).

### Weather shows an error

- Add a valid **OpenWeather API key** in Customize.
- Check city name or lat/lon and internet access.

### Apply / Save does nothing

1. **mt17** must be the active wallpaper in Lively.
2. Preset Manager must be running (`start.bat`).
3. Check **Settings** → wallpaper folder points to the installed copy Lively is actually running.
4. Reload the wallpaper once in Lively.

### Slideshow doesn’t change presets

1. Confirm `presets/slideshow.json` has `"enabled": true` and a non-empty `playlist`.
2. Interval minimum is **30 seconds**.
3. Slideshow runs in the wallpaper — edit/copy `slideshow.json` into the **installed** wallpaper folder if you use a library copy.
4. After manual **Apply**, re-save slideshow with **Enable** checked.

### Web UI doesn’t open

```bat
pip install flask
start.bat
```

Or use Tk: `python main.py --tk` (limited features — see table above).

### Python not found

Reinstall Python with **Add to PATH**, or run from a terminal where `python --version` works.

### Changes in dev folder don’t show on desktop

Copy updated files to `Library\wallpapers\{your-id}\` or point Lively at the dev folder directly.

---

## Quick reference

| Task | Steps |
|------|--------|
| Add wallpaper | Lively → Add → mt17 folder → Set as wallpaper |
| Change look | Lively → Customize |
| Save a theme (persistent) | Preset Manager → name → **Save current look** |
| Load a theme (persistent) | Preset Manager → select → **Apply to wallpaper** |
| Auto-rotate themes | Web UI → **Slideshow** → playlist → Enable → Save |
| Start Preset Manager | `preset-manager/start.bat` |
| Full Preset Manager UI | `pip install flask` → use web UI at :8767 |

---

## Credits & license

Built for personal use with **Lively Wallpaper**, **OpenWeather**, **GPT**, and **Cursor**. Wallpaper media, fonts, and bundled assets are your own — replace `media/`, `images/`, and `fonts/` as you like.

---

**Persian:** [README.fa.md](README.fa.md)

