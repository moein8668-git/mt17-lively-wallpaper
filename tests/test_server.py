import json
from urllib import error, request

from server import PresetApiServer
from preset_store import PresetStore


def call_json(url, method="GET", payload=None):
    body = None
    headers = {}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = request.Request(url, data=body, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=3) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except error.HTTPError as response:
        return response.code, json.loads(response.read().decode("utf-8"))


def test_http_api_rejects_invalid_filenames_and_accepts_valid_name(tmp_path):
    wallpaper = tmp_path / "wallpaper"
    wallpaper.mkdir()
    store = PresetStore(tmp_path / "backups", override_path=wallpaper)
    api = PresetApiServer(store, port=0)
    api.start()
    base_url = f"http://127.0.0.1:{api._httpd.server_port}"

    try:
        status, _ = call_json(f"{base_url}/api/preset/nested/theme.preset.json")
        assert status == 400

        status, _ = call_json(
            f"{base_url}/api/preset/save",
            method="POST",
            payload={
                "name": "Invalid",
                "file": "../outside.preset.json",
                "data": {"value": 1},
            },
        )
        assert status == 400
        assert not (tmp_path / "outside.preset.json").exists()

        status, body = call_json(
            f"{base_url}/api/preset/save",
            method="POST",
            payload={
                "name": "Valid",
                "file": "valid.preset.json",
                "data": {"value": 2},
            },
        )
        assert status == 200
        assert body["preset"]["file"] == "valid.preset.json"

        status, _ = call_json(
            f"{base_url}/api/preset/valid.preset.json",
            method="DELETE",
        )
        assert status == 200
        assert not (wallpaper / "presets" / "valid.preset.json").exists()
    finally:
        api.stop()


def test_status_with_persistence_marks_partial_result():
    from server import status_with_persistence

    status = status_with_persistence(
        {"ok": True, "action": "apply", "message": "Applied"},
        {
            "ok": False,
            "attempted": True,
            "files": [],
            "error": "SaveData missing",
        },
    )

    assert status["ok"] is True
    assert status["partial"] is True
    assert status["persistenceOk"] is False
    assert "SaveData missing" in status["message"]
