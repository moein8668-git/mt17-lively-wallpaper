import json
import webbrowser
import zipfile
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
from io import BytesIO

from config import (
    BACKUP_ROOT,
    create_preset_store,
    load_config,
    normalize_port,
    save_config,
    write_api_port_runtime,
)
from preset_labels import build_preset_view
from preset_package import (
    MAX_UPLOAD_BYTES,
    PresetPackager,
    parse_export_options,
)
from preset_store import PRESET_SUFFIX, PresetStore, validate_preset_filename
from server import PresetApiServer, status_with_persistence


def safe_preset_filename(filename: str) -> str:
    return validate_preset_filename(filename)


def read_upload_limited(upload) -> bytes:
    raw = upload.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise ValueError(
            f"Upload is too large (maximum {MAX_UPLOAD_BYTES} bytes)"
        )
    return raw


def create_services(config: dict):
    store = create_preset_store(config)
    api_port = normalize_port(config.get("apiPort", 8766))
    write_api_port_runtime(store.wallpaper_path, api_port)
    api_server = PresetApiServer(store, port=api_port)
    api_server.start()
    return store, api_server, api_port


def create_app(config: dict):
    store, api_server, api_port = create_services(config)
    web_port = int(config.get("webPort", 8767))

    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES + (1024 * 1024)
    app.config["APP_CONFIG"] = config
    app.config["STORE"] = store
    app.config["API_SERVER"] = api_server
    app.config["API_PORT"] = api_port
    app.config["WEB_PORT"] = web_port

    @app.errorhandler(413)
    def request_too_large(_error):
        return jsonify({"error": f"Upload is too large (maximum {MAX_UPLOAD_BYTES} bytes)"}), 400

    def current_config() -> dict:
        return app.config["APP_CONFIG"]

    def current_store() -> PresetStore:
        return app.config["STORE"]

    def current_packager() -> PresetPackager:
        store = current_store()
        return PresetPackager(store.wallpaper_path, store.presets_dir)

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

    @app.get("/api/preset/<path:filename>/download-zip")
    def download_preset_zip(filename):
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
            options = parse_export_options(args=request.args)
            buffer, download_name = current_packager().build_single_preset_zip(
                filename,
                data,
                entry,
                export_options=options,
            )
            return send_file(
                buffer,
                mimetype="application/zip",
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
                "scriptWallpaperPath": lively.get("scriptWallpaperPath", ""),
                "installedWallpaperPath": lively.get("installedWallpaperPath", ""),
                "pathSource": lively.get("pathSource", "script"),
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
        if "apiPort" in payload:
            cfg["apiPort"] = normalize_port(payload["apiPort"])

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
        new_api_port = normalize_port(cfg.get("apiPort", 8766))
        write_api_port_runtime(new_store.wallpaper_path, new_api_port)
        new_api_server = PresetApiServer(new_store, port=new_api_port)
        new_api_server.start()

        app.config["APP_CONFIG"] = cfg
        app.config["STORE"] = new_store
        app.config["API_SERVER"] = new_api_server
        app.config["API_PORT"] = new_api_port

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
        try:
            filename = safe_preset_filename(filename)
        except ValueError as error_info:
            return jsonify({"error": str(error_info)}), 400

        monitor = str(payload.get("monitor") or current_store().target_monitor)
        current_store().target_monitor = monitor
        result = current_store().write_command(
            "apply",
            monitor=monitor,
            name=name,
            file=filename,
        )
        current_api_server().last_status = status_with_persistence(
            {
                "ok": None,
                "message": "Working...",
                "action": None,
            },
            result.get("livelyPersistence"),
        )
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
        result = current_store().write_command(
            "capture",
            monitor=monitor,
            name=name,
            file=filename or None,
        )
        current_api_server().last_status = status_with_persistence(
            {
                "ok": None,
                "message": "Working...",
                "action": None,
            },
            result.get("livelyPersistence"),
        )
        return jsonify({"ok": True, **result})

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
            raw = read_upload_limited(upload).decode("utf-8")
            payload = json.loads(raw)

            if isinstance(payload, dict) and "presets" in payload and "manifest" in payload:
                return jsonify(
                    {"error": "That file is a full backup. Use Upload backup JSON instead."}
                ), 400

            if upload.filename.lower().endswith(".zip"):
                return jsonify(
                    {"error": "That file is a ZIP package. Use Upload preset ZIP instead."}
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

    @app.post("/api/preset/upload-zip")
    def upload_preset_zip():
        upload = request.files.get("file")

        if upload is None or not upload.filename:
            return jsonify({"error": "Choose a preset ZIP file first"}), 400

        try:
            result = current_packager().import_zip(
                read_upload_limited(upload),
                import_callback=lambda data, name, filename: current_store().import_preset_from_zip(
                    data,
                    name,
                    filename,
                ),
                restore_bundle_callback=current_store().restore_backup_bundle,
                write_slideshow_callback=current_store().write_slideshow,
                allowed_mode="single",
            )
            entry = result["preset"]
            asset_count = len(result.get("installedAssets", []))
            wallpaper_path = result.get("wallpaperPath", str(current_store().wallpaper_path))
            return jsonify(
                {
                    "ok": True,
                    "message": (
                        f"Imported '{entry['name']}' with {asset_count} asset file(s) "
                        f"into {wallpaper_path}"
                    ),
                    "preset": entry,
                    "presets": current_store().list_presets(),
                    "installedAssets": result.get("installedAssets", []),
                    "wallpaperPath": wallpaper_path,
                }
            )
        except zipfile.BadZipFile:
            return jsonify({"error": "Invalid ZIP file"}), 400
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

    @app.get("/api/backup/download-zip")
    def download_backup_zip():
        store = current_store()
        bundle = store.build_backup_bundle()
        options = parse_export_options(args=request.args)
        slideshow = None
        try:
            slideshow = store.read_slideshow()
        except (json.JSONDecodeError, ValueError):
            slideshow = None
        buffer, download_name = current_packager().build_full_backup_zip(
            bundle,
            slideshow=slideshow,
            export_options=options,
        )
        return send_file(
            buffer,
            mimetype="application/zip",
            as_attachment=True,
            download_name=download_name,
        )

    @app.post("/api/backup/upload")
    def upload_backup():
        upload = request.files.get("file")
        if upload is None or not upload.filename:
            return jsonify({"error": "Choose a backup JSON file first"}), 400

        if upload.filename.lower().endswith(".zip"):
            return jsonify(
                {"error": "That file is a ZIP package. Use Upload full backup ZIP instead."}
            ), 400

        try:
            raw = read_upload_limited(upload).decode("utf-8")
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

    @app.post("/api/backup/upload-zip")
    def upload_backup_zip():
        upload = request.files.get("file")
        if upload is None or not upload.filename:
            return jsonify({"error": "Choose a full backup ZIP file first"}), 400

        try:
            result = current_packager().import_zip(
                read_upload_limited(upload),
                import_callback=current_store().import_preset_data,
                restore_bundle_callback=current_store().restore_backup_bundle,
                write_slideshow_callback=current_store().write_slideshow,
                allowed_mode="full",
            )

            count = result.get("restoredPresets", 0)
            asset_count = len(result.get("installedAssets", []))
            wallpaper_path = result.get("wallpaperPath", str(current_store().wallpaper_path))
            slideshow_note = (
                " Slideshow settings restored."
                if result.get("slideshowRestored")
                else ""
            )
            return jsonify(
                {
                    "ok": True,
                    "message": (
                        f"Restored {count} preset(s) and {asset_count} asset file(s) "
                        f"into {wallpaper_path}.{slideshow_note}"
                    ),
                    "presets": current_store().list_presets(),
                    "installedAssets": result.get("installedAssets", []),
                    "wallpaperPath": wallpaper_path,
                }
            )
        except zipfile.BadZipFile:
            return jsonify({"error": "Invalid ZIP file"}), 400
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
