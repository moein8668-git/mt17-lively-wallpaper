from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from preset_package import (
    MAX_UPLOAD_BYTES,
    MAX_ZIP_MEMBERS,
    PresetPackager,
    is_safe_zip_member,
)
from preset_store import PresetStore


def test_zip_member_safety_checks():
    assert is_safe_zip_member("presets/theme.preset.json")
    assert is_safe_zip_member("./media/background.webm")
    assert not is_safe_zip_member("media/../outside.txt")
    assert not is_safe_zip_member("media/../../absolute.txt")
    assert not is_safe_zip_member("media/")


def test_single_package_round_trip_installs_assets_and_preset(tmp_path):
    source_wallpaper = tmp_path / "source"
    source_wallpaper.mkdir()
    source_store = PresetStore(tmp_path / "source-backups", override_path=source_wallpaper)
    asset = source_wallpaper / "media" / "background.webm"
    asset.parent.mkdir(parents=True, exist_ok=True)
    asset.write_bytes(b"video")

    source_entry = source_store.save_preset(
        "Ocean",
        {"BackgroundSource": r"C:\wallpaper\media\background.webm"},
    )
    source_packager = PresetPackager(source_wallpaper, source_store.presets_dir)
    package, download_name = source_packager.build_single_preset_zip(
        source_entry["file"],
        source_store.read_preset(source_entry["file"]),
        source_entry,
    )
    assert download_name == "mt17-preset-Ocean.zip"

    with ZipFile(BytesIO(package.getvalue())) as archive:
        assert "package.json" in archive.namelist()
        assert "presets/Ocean.preset.json" in archive.namelist()
        assert "media/background.webm" in archive.namelist()

    target_wallpaper = tmp_path / "target"
    target_wallpaper.mkdir()
    target_store = PresetStore(tmp_path / "target-backups", override_path=target_wallpaper)
    target_packager = PresetPackager(target_wallpaper, target_store.presets_dir)
    result = target_packager.import_zip(
        package.getvalue(),
        import_callback=lambda data, name, filename: target_store.import_preset_from_zip(
            data, name, filename
        ),
        restore_bundle_callback=target_store.restore_backup_bundle,
    )

    assert result["packageType"] == "single"
    assert result["preset"]["name"] == "Ocean"
    assert (target_wallpaper / "media" / "background.webm").read_bytes() == b"video"
    assert target_store.read_preset("Ocean.preset.json") == {
        "BackgroundSource": r"C:\wallpaper\media\background.webm"
    }


def test_zip_import_rejects_unsafe_members(tmp_path):
    package = BytesIO()
    with ZipFile(package, "w") as archive:
        archive.writestr("presets/../escape.preset.json", "{}")

    wallpaper = tmp_path / "wallpaper"
    wallpaper.mkdir()
    store = PresetStore(tmp_path / "backups", override_path=wallpaper)
    packager = PresetPackager(tmp_path / "wallpaper", store.presets_dir)
    with pytest.raises(ValueError, match="unsafe"):
        packager.import_zip(
            package.getvalue(),
            import_callback=lambda data, name, filename: None,
            restore_bundle_callback=store.restore_backup_bundle,
        )


def test_wrong_mode_zip_does_not_install_assets_or_change_presets(tmp_path):
    wallpaper = tmp_path / "wallpaper"
    wallpaper.mkdir()
    store = PresetStore(tmp_path / "backups", override_path=wallpaper)
    store.save_preset("Existing", {"value": "sentinel"})
    (wallpaper / "media").mkdir()
    (wallpaper / "media" / "asset.webm").write_bytes(b"original")

    package = BytesIO()
    with ZipFile(package, "w", ZIP_DEFLATED) as archive:
        archive.writestr("package.json", '{"packageType": "full"}')
        archive.writestr(
            "presets/one.preset.json",
            '{"value": 1}',
        )
        archive.writestr(
            "presets/two.preset.json",
            '{"value": 2}',
        )
        archive.writestr("media/asset.webm", b"replacement")

    packager = PresetPackager(wallpaper, store.presets_dir)
    with pytest.raises(ValueError, match="full backup"):
        packager.import_zip(
            package.getvalue(),
            import_callback=lambda data, name, filename: None,
            restore_bundle_callback=store.restore_backup_bundle,
            allowed_mode="single",
        )

    assert store.read_preset("Existing.preset.json") == {"value": "sentinel"}
    assert (wallpaper / "media" / "asset.webm").read_bytes() == b"original"


def test_zip_upload_limits_are_checked_before_processing(tmp_path):
    wallpaper = tmp_path / "wallpaper"
    wallpaper.mkdir()
    store = PresetStore(tmp_path / "backups", override_path=wallpaper)
    packager = PresetPackager(wallpaper, store.presets_dir)

    with pytest.raises(ValueError, match="too large"):
        packager.import_zip(
            b"x" * (MAX_UPLOAD_BYTES + 1),
            import_callback=lambda data, name, filename: None,
            restore_bundle_callback=store.restore_backup_bundle,
        )

    package = BytesIO()
    with ZipFile(package, "w", ZIP_DEFLATED) as archive:
        for index in range(MAX_ZIP_MEMBERS + 1):
            archive.writestr(f"media/{index}.bin", b"x")
    with pytest.raises(ValueError, match="too many"):
        packager.import_zip(
            package.getvalue(),
            import_callback=lambda data, name, filename: None,
            restore_bundle_callback=store.restore_backup_bundle,
        )
