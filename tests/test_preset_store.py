import json

import pytest

from preset_store import (
    SLIDESHOW_MAX_CROSSFADE,
    SLIDESHOW_MAX_INTERVAL,
    SLIDESHOW_MIN_CROSSFADE,
    SLIDESHOW_MIN_INTERVAL,
    PresetStore,
)


def make_store(tmp_path):
    wallpaper = tmp_path / "wallpaper"
    backups = tmp_path / "backups"
    wallpaper.mkdir()
    return PresetStore(backups, override_path=wallpaper)


def test_slideshow_defaults_and_validation_bounds(tmp_path):
    store = make_store(tmp_path)

    assert store.read_slideshow() == {
        "version": 1,
        "enabled": False,
        "intervalSeconds": 300,
        "order": "sequential",
        "playlist": [],
        "pausedUntilManualResume": False,
        "crossfadeSeconds": 1.2,
    }

    validated = store.write_slideshow(
        {
            "enabled": True,
            "intervalSeconds": 1,
            "crossfadeSeconds": 99,
            "order": "RANDOM",
            "playlist": [],
        }
    )
    assert validated["enabled"] is False
    assert validated["intervalSeconds"] == SLIDESHOW_MIN_INTERVAL
    assert validated["crossfadeSeconds"] == SLIDESHOW_MAX_CROSSFADE
    assert validated["order"] == "random"

    validated = store.write_slideshow(
        {
            "intervalSeconds": SLIDESHOW_MAX_INTERVAL + 1,
            "crossfadeSeconds": -1,
            "order": "shuffle",
        }
    )
    assert validated["intervalSeconds"] == SLIDESHOW_MAX_INTERVAL
    assert validated["crossfadeSeconds"] == SLIDESHOW_MIN_CROSSFADE

    with pytest.raises(ValueError, match="order"):
        store.write_slideshow({"order": "invalid"})


def test_preset_save_list_read_manifest_and_duplicate_naming(tmp_path):
    store = make_store(tmp_path)
    data = {"show_clock1": True, "backgroundColor": "rgba(1, 2, 3, 1)"}

    entry = store.save_preset("Sunset Theme", data)
    assert entry["file"] == "Sunset-Theme.preset.json"
    assert store.read_preset(entry["file"]) == data
    assert [item["name"] for item in store.list_presets()] == ["Sunset Theme"]

    duplicate = store.duplicate_preset(entry["file"])
    assert duplicate["name"] == "Sunset Theme Copy"
    assert duplicate["file"] == "Sunset-Theme-Copy.preset.json"
    assert len(store.list_presets()) == 2

    manifest = json.loads(store.manifest_path.read_text(encoding="utf-8"))
    assert {item["file"] for item in manifest["presets"]} == {
        "Sunset-Theme.preset.json",
        "Sunset-Theme-Copy.preset.json",
    }


def test_backup_bundle_restores_valid_data(tmp_path):
    store = make_store(tmp_path)
    entry = store.save_preset("Restore Me", {"show_weather": True})
    bundle = store.build_backup_bundle()

    assert bundle["version"] == 1
    assert bundle["presets"][entry["file"]] == {"show_weather": True}
    store.delete_preset(entry["file"])
    assert store.list_presets() == []

    assert store.restore_backup_bundle(bundle) == 1
    assert store.read_preset(entry["file"]) == {"show_weather": True}
    assert store.list_presets()[0]["file"] == entry["file"]


def test_preset_filename_validation_blocks_traversal_and_wrong_suffix(tmp_path):
    store = make_store(tmp_path)
    outside = tmp_path / "outside.preset.json"
    outside.write_text('{"sentinel": true}', encoding="utf-8")

    for filename in (
        "../outside.preset.json",
        "nested/theme.preset.json",
        str(outside),
        "theme.json",
    ):
        with pytest.raises(ValueError):
            store.read_preset(filename)
        with pytest.raises(ValueError):
            store.save_preset("Theme", {}, filename=filename)
        with pytest.raises(ValueError):
            store.delete_preset(filename)

    with pytest.raises(ValueError):
        store.restore_backup_bundle(
            {
                "manifest": {"version": 1, "presets": []},
                "presets": {"../outside.preset.json": {"changed": True}},
            }
        )
    assert outside.read_text(encoding="utf-8") == '{"sentinel": true}'


def test_valid_explicit_filename_stays_inside_presets(tmp_path):
    store = make_store(tmp_path)

    entry = store.save_preset("Theme", {"value": 1}, filename="theme.preset.json")

    assert entry["file"] == "theme.preset.json"
    assert (store.presets_dir / "theme.preset.json").read_text(encoding="utf-8")


def test_backup_restore_preserves_command_and_is_failure_safe(tmp_path, monkeypatch):
    store = make_store(tmp_path)
    store.save_preset("Existing", {"value": "old"})
    command = store.presets_dir / "_command.json"
    command.write_text('{"action": "capture"}', encoding="utf-8")
    bundle = {
        "manifest": {
            "version": 1,
            "presets": [
                {
                    "id": "replacement",
                    "name": "Replacement",
                    "file": "replacement.preset.json",
                }
            ],
        },
        "presets": {"replacement.preset.json": {"value": "new"}},
    }

    def fail_replace(_stage):
        raise OSError("injected restore failure")

    monkeypatch.setattr(store, "_replace_presets_directory", fail_replace)
    with pytest.raises(OSError, match="injected"):
        store.restore_backup_bundle(bundle)

    assert store.read_preset("Existing.preset.json") == {"value": "old"}
    assert command.read_text(encoding="utf-8") == '{"action": "capture"}'


def test_savedata_failure_is_explicit_partial_result(tmp_path, monkeypatch):
    store = make_store(tmp_path)

    def missing_savedata(_preset, _monitor):
        raise FileNotFoundError("No Lively SaveData found for monitor '1'")

    monkeypatch.setattr(store.lively_sync, "apply_preset", missing_savedata)
    entry = store.save_preset("Offline", {"show_weather": True})

    assert entry["livelyPersistence"]["attempted"] is True
    assert entry["livelyPersistence"]["ok"] is False
    assert "No Lively SaveData" in entry["livelyPersistence"]["error"]
    assert store.read_preset(entry["file"]) == {"show_weather": True}


def test_savedata_success_reports_updated_files(tmp_path, monkeypatch):
    store = make_store(tmp_path)
    updated = tmp_path / "monitor" / "LivelyProperties.json"

    monkeypatch.setattr(
        store.lively_sync,
        "apply_preset",
        lambda _preset, _monitor: [updated],
    )
    entry = store.save_preset("Online", {"show_weather": True})

    assert entry["livelyPersistence"] == {
        "ok": True,
        "attempted": True,
        "files": [str(updated)],
        "error": None,
    }
