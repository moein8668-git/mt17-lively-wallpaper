import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from preset_store import PresetStore


class PresetApiHandler(BaseHTTPRequestHandler):
    store: PresetStore | None = None
    api_server: "PresetApiServer | None" = None

    def log_message(self, format, *args):
        return

    def _send_json(self, status: int, payload: dict | list):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            if path == "/api/health":
                lively_paths = self.store.lively_sync.path_summary()
                self._send_json(
                    200,
                    {
                        "ok": True,
                        "presetsDir": str(self.store.presets_dir),
                        "lively": lively_paths,
                    },
                )
                return

            if path == "/api/lively/paths":
                self._send_json(200, self.store.lively_sync.path_summary())
                return

            if path == "/api/presets":
                self._send_json(200, {"presets": self.store.list_presets()})
                return

            if path == "/api/slideshow":
                self._send_json(200, self.store.slideshow_with_labels())
                return

            if path == "/api/status":
                self._send_json(200, PresetApiHandler.api_server.last_status)
                return

            if path.startswith("/api/preset/"):
                filename = path.split("/api/preset/", 1)[1]
                data = self.store.read_preset(filename)
                self._send_json(200, data)
                return
        except FileNotFoundError:
            self._send_json(404, {"error": "Preset not found"})
            return
        except Exception as error:
            self._send_json(500, {"error": str(error)})
            return

        self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            payload = self._read_json()

            if path == "/api/preset/save":
                name = payload.get("name", "").strip()
                data = payload.get("data")
                filename = payload.get("file")
                if not name:
                    self._send_json(400, {"error": "Preset name is required"})
                    return
                if not isinstance(data, dict):
                    self._send_json(400, {"error": "Preset data is required"})
                    return
                entry = self.store.save_preset(name, data, filename)
                message = f"Saved '{entry['name']}'"
                lively_saved = entry.get("livelySavedataFiles") or []
                if lively_saved:
                    message += (
                        f" (Lively monitor {entry.get('livelyMonitor', self.store.target_monitor)}"
                        f" saved)"
                    )
                status = {
                    "ok": True,
                    "action": "capture",
                    "message": message,
                    "name": entry["name"],
                    "file": entry["file"],
                }
                if PresetApiHandler.api_server is not None:
                    PresetApiHandler.api_server.last_status = status
                self._send_json(200, {"ok": True, "preset": entry, **status})
                return

            if path == "/api/preset/rename":
                filename = payload.get("file")
                new_name = payload.get("name", "").strip()
                if not filename or not new_name:
                    self._send_json(400, {"error": "file and name are required"})
                    return
                entry = self.store.rename_preset(filename, new_name)
                self._send_json(200, {"ok": True, "preset": entry})
                return

            if path == "/api/preset/duplicate":
                filename = payload.get("file")
                if not filename:
                    self._send_json(400, {"error": "file is required"})
                    return
                entry = self.store.duplicate_preset(filename)
                self._send_json(200, {"ok": True, "preset": entry})
                return

            if path == "/api/backup":
                target = self.store.create_backup()
                self._send_json(200, {"ok": True, "backup": str(target)})
                return

            if path == "/api/restore":
                restored = self.store.restore_latest_backup()
                if restored is None:
                    self._send_json(404, {"error": "No backup found"})
                    return
                self._send_json(
                    200,
                    {
                        "ok": True,
                        "restoredFrom": str(restored),
                        "presets": self.store.list_presets(),
                    },
                )
                return

            if path == "/api/status":
                PresetApiHandler.api_server.last_status = payload
                self._send_json(200, {"ok": True})
                return

            if path == "/api/command/done":
                self.store.clear_command()
                self._send_json(200, {"ok": True})
                return

            if path == "/api/slideshow":
                self.store.write_slideshow(payload)
                self._send_json(200, {"ok": True, "slideshow": self.store.slideshow_with_labels()})
                return
        except ValueError as error:
            self._send_json(400, {"error": str(error)})
            return
        except FileExistsError as error:
            self._send_json(409, {"error": str(error)})
            return
        except FileNotFoundError:
            self._send_json(404, {"error": "Preset not found"})
            return
        except Exception as error:
            self._send_json(500, {"error": str(error)})
            return

        self._send_json(404, {"error": "Not found"})

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            if path.startswith("/api/preset/"):
                filename = path.split("/api/preset/", 1)[1]
                self.store.delete_preset(filename)
                self._send_json(200, {"ok": True})
                return
        except FileNotFoundError:
            self._send_json(404, {"error": "Preset not found"})
            return
        except Exception as error:
            self._send_json(500, {"error": str(error)})
            return

        self._send_json(404, {"error": "Not found"})


class PresetApiServer:
    def __init__(self, store: PresetStore, host: str = "127.0.0.1", port: int = 8766):
        self.store = store
        self.host = host
        self.port = port
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self.last_status = {"ok": True, "message": "Ready"}

    @property
    def running(self) -> bool:
        return self._httpd is not None

    def start(self):
        if self.running:
            return

        PresetApiHandler.store = self.store
        PresetApiHandler.api_server = self
        self._httpd = ThreadingHTTPServer((self.host, self.port), PresetApiHandler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

    def stop(self):
        if not self.running:
            return
        self._httpd.shutdown()
        self._httpd.server_close()
        self._httpd = None
        self._thread = None
