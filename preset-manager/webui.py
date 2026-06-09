import json
import webbrowser
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
from io import BytesIO

from config import BACKUP_ROOT, create_preset_store, load_config, save_config
from preset_labels import build_preset_view
from preset_store import PRESET_SUFFIX, PresetStore
from server import PresetApiServer


def safe_preset_filename(filename: str) -> str:
    name = Path(filename).name
    if not name.endswith(PRESET_SUFFIX):
        raise ValueError("Invalid preset file")
    return name


def create_services(config: dict):
    store = create_preset_store(config)
    api_port = int(config.get("apiPort", 8766))
    api_server = PresetApiServer(store, port=api_port)
    api_server.start()
    return store, api_server, api_port


def create_app(config: dict):
    store, api_server, api_port = create_services(config)
    web_port = int(config.get("webPort", 8767))

    app = Flask(__name__)
    app.config["APP_CONFIG"] = config
    app.config["STORE"] = store
    app.config["API_SERVER"] = api_server
    app.config["API_PORT"] = api_port
    app.config["WEB_PORT"] = web_port

    def current_config() -> dict:
        return app.config["APP_CONFIG"]

    def current_store() -> PresetStore:
        return app.config["STORE"]

    def current_api_server() -> PresetApiServer:
        return app.config["API_SERVER"]

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            api_port=app.config["API_PORT"],
            web_port=app.config["WEB_PORT"],
            wallpaper_path=str(current_store().wallpaper_path),
        )

    @app.get("/api/presets")
    def list_presets():
        return jsonify({"presets": current_store().list_presets()})

    @app.get("/api/slideshow")
    def get_slideshow():
        return jsonify(current_store().slideshow_with_labels())

    @app.post("/api/slideshow")
    def save_slideshow():
        payload = request.get_json(silent=True) or {}
        try:
            current_store().write_slideshow(payload)
            return jsonify({"ok": True, "slideshow": current_store().slideshow_with_labels()})
        except ValueError as error_info:
            return jsonify({"error": str(error_info)}), 400

    @app.get("/api/wallpaper/thumbnail")
    def wallpaper_thumbnail():
        info_path = current_store().wallpaper_path / "LivelyInfo.json"
        thumb_name = "thumbnail.jpg"
        title = "mt17"

        if info_path.exists():
            with info_path.open("r", encoding="utf-8") as handle:
                info = json.load(handle)
            thumb_name = info.get("Thumbnail") or thumb_name
            title = info.get("Title") or title

        thumb_path = current_store().wallpaper_path / thumb_name
        if not thumb_path.exists():
            return jsonify({"error": "Thumbnail not found", "title": title}), 404

        return send_file(thumb_path)

    @app.get("/api/preset/<path:filename>")
    def get_preset(filename):
        try:
            filename = safe_preset_filename(filename)
            data = current_store().read_preset(filename)
            entry = next(
                (
                    item
                    for item in current_store().list_presets()
                    if item["file"] == filename
                ),
                {"name": filename[: -len(PRESET_SUFFIX)], "file": filename},
            )
            return jsonify(
                {
                    "preset": entry,
                    "groups": build_preset_view(data),
                }
            )
        except ValueError as error_info:
            return jsonify({"error": str(error_info)}), 400
        except FileNotFoundError:
            return jsonify({"error": "Preset not found"}), 404

    @app.get("/api/preset/<path:filename>/download")
    def download_preset(filename):
        try:
            filename = safe_preset_filename(filename)
            data = current_store().read_preset(filename)
            entry = next(
                (
                    item
                    for item in current_store().list_presets()
                    if item["file"] == filename
                ),
                {"name": filename[: -len(PRESET_SUFFIX)], "file": filename},
            )
            download_name = entry["name"].strip().replace(" ", "-") + ".preset.json"
            payload = json.dumps(data, indent=2).encode("utf-8")
            return send_file(
                BytesIO(payload),
                mimetype="application/json",
                as_attachment=True,
                download_name=download_name,
            )
        except ValueError as error_info:
            return jsonify({"error": str(error_info)}), 400
        except FileNotFoundError:
            return jsonify({"error": "Preset not found"}), 404

    @app.get("/api/status")
    def get_status():
        return jsonify(current_api_server().last_status)

    @app.get("/api/health")
    def health():
        return jsonify(
            {
                "ok": True,
                "presetsDir": str(current_store().presets_dir),
                "wallpaperPath": str(current_store().wallpaper_path),
                "apiPort": app.config["API_PORT"],
                "lively": current_store().lively_sync.path_summary(),
            }
        )

    @app.get("/api/lively/paths")
    def lively_paths():
        return jsonify(current_store().lively_sync.path_summary())

    @app.get("/api/lively/monitors")
    def lively_monitors():
        return jsonify({"monitors": current_store().list_monitors()})

    @app.get("/api/settings")
    def get_settings():
        cfg = current_config()
        store = current_store()
        lively = store.lively_sync.path_summary()
        return jsonify(
            {
                "targetMonitor": store.target_monitor,
                "wallpaperPathOverride": cfg.get("wallpaperPathOverride", ""),
                "installedWallpaperPath": lively.get("installedWallpaperPath", ""),
                "savedataDir": lively.get("savedataDir", ""),
                "monitors": lively.get("monitors", []),
                "apiPort": int(cfg.get("apiPort", 8766)),
                "webPort": int(cfg.get("webPort", 8767)),
            }
        )

    @app.post("/api/settings")
    def update_settings():
        payload = request.get_json(silent=True) or {}
        cfg = load_config()

        if "targetMonitor" in payload:
            cfg["targetMonitor"] = str(payload["targetMonitor"])

        override = payload.get("wallpaperPathOverride")
        if override is not None:
            override = str(override).strip()
            if override:
                path = Path(override)
                if not path.exists():
                    return jsonify({"error": "Override folder does not exist"}), 400
                cfg["wallpaperPathOverride"] = str(path)
            else:
                cfg.pop("wallpaperPathOverride", None)

        save_config(cfg)
        cfg = load_config()

        new_store = create_preset_store(cfg)
        current_api_server().stop()
        new_api_server = PresetApiServer(new_store, port=app.config["API_PORT"])
        new_api_server.start()

        app.config["APP_CONFIG"] = cfg
        app.config["STORE"] = new_store
        app.config["API_SERVER"] = new_api_server

        return jsonify(
            {
                "ok": True,
                "targetMonitor": new_store.target_monitor,
                "installedWallpaperPath": str(new_store.wallpaper_path),
                "monitors": new_store.list_monitors(),
            }
        )

    @app.post("/api/command/apply")
    def command_apply():
        payload = request.get_json(silent=True) or {}
        name = str(payload.get("name", "")).strip()
        filename = str(payload.get("file", "")).strip()
        if not filename:
            return jsonify({"error": "Preset file is required"}), 400

        monitor = str(payload.get("monitor") or current_store().target_monitor)
        current_store().target_monitor = monitor
        result = current_store().write_command(
            "apply",
            monitor=monitor,
            name=name,
            file=filename,
        )
        current_api_server().last_status = {
            "ok": None,
            "message": "Working...",
            "action": None,
        }
        return jsonify({"ok": True, **result})

    @app.post("/api/command/capture")
    def command_capture():
        payload = request.get_json(silent=True) or {}
        name = str(payload.get("name", "")).strip()
        filename = payload.get("file")
        if not name:
            return jsonify({"error": "Preset name is required"}), 400

        monitor = str(payload.get("monitor") or current_store().target_monitor)
        current_store().target_monitor = monitor
        current_store().write_command(
            "capture",
            monitor=monitor,
            name=name,
            file=filename or None,
        )
        current_api_server().last_status = {
            "ok": None,
            "message": "Working...",
            "action": None,
        }
        return jsonify({"ok": True})

    @app.post("/api/preset/rename")
    def rename_preset():
        payload = request.get_json(silent=True) or {}
        filename = str(payload.get("file", "")).strip()
        new_name = str(payload.get("name", "")).strip()
        if not filename or not new_name:
            return jsonify({"error": "file and name are required"}), 400
        try:
            entry = current_store().rename_preset(filename, new_name)
            return jsonify({"ok": True, "preset": entry})
        except Exception as error_info:
            return jsonify({"error": str(error_info)}), 400

    @app.post("/api/preset/duplicate")
    def duplicate_preset():
        payload = request.get_json(silent=True) or {}
        filename = str(payload.get("file", "")).strip()
        if not filename:
            return jsonify({"error": "file is required"}), 400
        try:
            entry = current_store().duplicate_preset(filename)
            return jsonify({"ok": True, "preset": entry})
        except Exception as error_info:
            return jsonify({"error": str(error_info)}), 400

    @app.post("/api/preset/delete")
    def delete_preset():
        payload = request.get_json(silent=True) or {}
        filename = str(payload.get("file", "")).strip()
        if not filename:
            return jsonify({"error": "file is required"}), 400
        try:
            current_store().delete_preset(filename)
            return jsonify({"ok": True})
        except Exception as error_info:
            return jsonify({"error": str(error_info)}), 400

    @app.post("/api/preset/upload")
    def upload_preset():
        upload = request.files.get("file")
        preset_name = (request.form.get("name") or "").strip()

        if upload is None or not upload.filename:
            return jsonify({"error": "Choose a preset JSON file first"}), 400

        try:
            raw = upload.read().decode("utf-8")
            payload = json.loads(raw)

            if isinstance(payload, dict) and "presets" in payload and "manifest" in payload:
                return jsonify(
                    {"error": "That file is a full backup. Use Upload backup JSON instead."}
                ), 400

            if not isinstance(payload, dict):
                return jsonify({"error": "Preset file must be a JSON object"}), 400

            entry = current_store().import_preset_data(
                payload,
                preset_name or Path(upload.filename).stem.replace("-", " "),
            )
            return jsonify(
                {
                    "ok": True,
                    "message": f"Imported '{entry['name']}'",
                    "preset": entry,
                    "presets": current_store().list_presets(),
                }
            )
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON file"}), 400
        except ValueError as error_info:
            return jsonify({"error": str(error_info)}), 400
        except Exception as error_info:
            return jsonify({"error": str(error_info)}), 500

    @app.post("/api/backup")
    def create_backup():
        try:
            target = current_store().create_backup()
            return jsonify({"ok": True, "backup": str(target)})
        except Exception as error_info:
            return jsonify({"error": str(error_info)}), 500

    @app.post("/api/restore")
    def restore_backup():
        restored = current_store().restore_latest_backup()
        if restored is None:
            return jsonify({"error": "No backup found"}), 404
        return jsonify(
            {
                "ok": True,
                "restoredFrom": str(restored),
                "presets": current_store().list_presets(),
            }
        )

    @app.get("/api/backup/download")
    def download_backup():
        bundle = current_store().build_backup_bundle()
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        payload = json.dumps(bundle, indent=2).encode("utf-8")
        return send_file(
            BytesIO(payload),
            mimetype="application/json",
            as_attachment=True,
            download_name=f"mt17-presets-backup-{stamp}.json",
        )

    @app.post("/api/backup/upload")
    def upload_backup():
        upload = request.files.get("file")
        if upload is None or not upload.filename:
            return jsonify({"error": "Choose a backup JSON file first"}), 400

        try:
            raw = upload.read().decode("utf-8")
            bundle = json.loads(raw)
            count = current_store().restore_backup_bundle(bundle)
            return jsonify(
                {
                    "ok": True,
                    "message": f"Restored {count} preset(s) from upload",
                    "presets": current_store().list_presets(),
                }
            )
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON file"}), 400
        except ValueError as error_info:
            return jsonify({"error": str(error_info)}), 400
        except Exception as error_info:
            return jsonify({"error": str(error_info)}), 500

    return app, api_server


def run_webui(config: dict, open_browser: bool = True):
    app, api_server = create_app(config)
    web_port = int(config.get("webPort", 8767))
    url = f"http://127.0.0.1:{web_port}"

    print(f"mt17 Preset Manager — Web UI at {url}")
    print(f"Wallpaper API listening on http://127.0.0.1:{config.get('apiPort', 8766)}")

    if open_browser:
        webbrowser.open(url)

    try:
        app.run(host="127.0.0.1", port=web_port, debug=False, use_reloader=False)
    finally:
        api_server.stop()
