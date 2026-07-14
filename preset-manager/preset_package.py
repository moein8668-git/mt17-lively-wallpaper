import copy
import json
import random
import re
import shutil
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path, PurePosixPath

from lively_properties import basename_from_media_path
from preset_store import (
    MANIFEST_NAME,
    PRESET_SUFFIX,
    SLIDESHOW_FILE,
    sanitize_filename,
    utc_now_iso,
)


PACKAGE_MANIFEST = "package.json"
PACKAGE_VERSION = 1
ASSET_FOLDERS = ("media", "images", "fonts")
MAX_UPLOAD_BYTES = 32 * 1024 * 1024
MAX_ZIP_MEMBERS = 256
MAX_ZIP_MEMBER_BYTES = 32 * 1024 * 1024
MAX_ZIP_UNCOMPRESSED_BYTES = 128 * 1024 * 1024


def parse_export_options(payload: dict | None = None, *, args=None) -> dict:
    """Read blankApiKey / randomizeLocation from JSON body or query args."""

    def _flag(source, key: str) -> bool:
        if source is None:
            return False
        if key not in source:
            return False
        value = source.get(key)
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in ("1", "true", "yes", "on")

    blank_api = _flag(payload, "blankApiKey") or _flag(args, "blankApiKey")
    randomize_location = _flag(payload, "randomizeLocation") or _flag(
        args, "randomizeLocation"
    )
    return {
        "blankApiKey": blank_api,
        "randomizeLocation": randomize_location,
    }


def sanitize_preset_for_export(
    preset: dict,
    *,
    blank_api_key: bool = False,
    randomize_location: bool = False,
) -> dict:
    data = copy.deepcopy(preset)
    if blank_api_key:
        data["apiKey"] = ""
    if randomize_location:
        data["Lat"] = round(random.uniform(-60.0, 60.0), 2)
        data["Lon"] = round(random.uniform(-180.0, 180.0), 2)
        data["city"] = "City"
        data["UseCity"] = False
    return data


def collect_assets_from_preset(preset: dict) -> dict[str, set[str]]:
    assets = {folder: set() for folder in ASSET_FOLDERS}

    video = preset.get("BackgroundSource")
    if video:
        assets["media"].add(basename_from_media_path(str(video)))

    image = preset.get("BackgroundImageSource")
    if image:
        assets["images"].add(basename_from_media_path(str(image)))

    font_files = preset.get("fontFiles")
    if isinstance(font_files, dict):
        for value in font_files.values():
            if value:
                assets["fonts"].add(basename_from_media_path(str(value)))

    return assets


def merge_asset_maps(*maps: dict[str, set[str]]) -> dict[str, set[str]]:
    merged = {folder: set() for folder in ASSET_FOLDERS}
    for asset_map in maps:
        for folder in ASSET_FOLDERS:
            merged[folder].update(asset_map.get(folder, set()))
    return merged


def normalize_zip_member(name: str) -> str:
    normalized = name.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def is_safe_zip_member(name: str) -> bool:
    normalized = normalize_zip_member(name)
    if not normalized or normalized.endswith("/"):
        return False
    path = PurePosixPath(normalized)
    if path.is_absolute():
        return False
    if path.parts and ":" in path.parts[0]:
        return False
    return ".." not in path.parts


def _safe_slug(name: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", name.strip()).replace(" ", "-")
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    return cleaned or "preset"


def preset_name_from_package(
    package_meta: dict,
    manifest_entry: dict | None,
    filename: str,
) -> str:
    """Display name from package.json presetFile, then manifest, then filename."""
    preset_file = str(
        package_meta.get("presetFile")
        or (manifest_entry or {}).get("file")
        or filename
    )
    if preset_file.endswith(PRESET_SUFFIX):
        return preset_file[: -len(PRESET_SUFFIX)]
    return Path(preset_file).stem


def preset_filename_from_package(
    package_meta: dict,
    manifest_entry: dict | None,
    filename: str,
) -> str:
    """Keep the original preset filename from the package when possible."""
    preset_file = str(
        package_meta.get("presetFile")
        or (manifest_entry or {}).get("file")
        or filename
    )
    preset_file = Path(preset_file).name
    if preset_file.endswith(PRESET_SUFFIX):
        return preset_file
    return sanitize_filename(preset_file)


class PresetPackager:
    def __init__(self, wallpaper_path: Path, presets_dir: Path):
        self.wallpaper_path = Path(wallpaper_path)
        self.presets_dir = Path(presets_dir)

    def _write_assets_to_zip(
        self,
        archive: zipfile.ZipFile,
        assets: dict[str, set[str]],
    ) -> tuple[list[str], list[str]]:
        included: list[str] = []
        missing: list[str] = []

        for folder in ASSET_FOLDERS:
            for filename in sorted(assets.get(folder, set())):
                if not filename:
                    continue
                source = self.wallpaper_path / folder / filename
                archive_name = f"{folder}/{filename}"
                if not source.is_file():
                    missing.append(archive_name)
                    continue
                archive.write(source, archive_name)
                included.append(archive_name)

        return included, missing

    def build_single_preset_zip(
        self,
        filename: str,
        preset_data: dict,
        entry: dict,
        *,
        export_options: dict | None = None,
    ) -> tuple[BytesIO, str]:
        options = export_options or {}
        sanitized = sanitize_preset_for_export(
            preset_data,
            blank_api_key=options.get("blankApiKey", False),
            randomize_location=options.get("randomizeLocation", False),
        )
        assets = collect_assets_from_preset(sanitized)
        manifest = {
            "version": 1,
            "presets": [
                {
                    "id": entry.get("id") or _safe_slug(entry.get("name", filename)).lower(),
                    "name": entry.get("name", filename[: -len(PRESET_SUFFIX)]),
                    "file": filename,
                    "updated": utc_now_iso(),
                }
            ],
        }

        package_meta = {
            "version": PACKAGE_VERSION,
            "packageType": "single",
            "exportedAt": utc_now_iso(),
            "exportOptions": options,
            "presetFile": filename,
        }

        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(PACKAGE_MANIFEST, json.dumps(package_meta, indent=2))
            archive.writestr(
                f"presets/{filename}",
                json.dumps(sanitized, indent=2),
            )
            archive.writestr(
                f"presets/{MANIFEST_NAME}",
                json.dumps(manifest, indent=2),
            )
            included, missing = self._write_assets_to_zip(archive, assets)
            if missing:
                package_meta["missingAssets"] = missing
                package_meta["includedAssets"] = included
                # Rewrite manifest with asset info
                archive.writestr(PACKAGE_MANIFEST, json.dumps(package_meta, indent=2))

        download_name = f"mt17-preset-{_safe_slug(entry.get('name', filename))}.zip"
        buffer.seek(0)
        return buffer, download_name

    def build_full_backup_zip(
        self,
        bundle: dict,
        *,
        slideshow: dict | None = None,
        export_options: dict | None = None,
    ) -> tuple[BytesIO, str]:
        options = export_options or {}
        manifest = bundle.get("manifest") or {"version": 1, "presets": []}
        raw_presets = bundle.get("presets") or {}

        sanitized_presets: dict[str, dict] = {}
        asset_maps: list[dict[str, set[str]]] = []
        for filename, data in raw_presets.items():
            if not isinstance(filename, str) or not filename.endswith(PRESET_SUFFIX):
                continue
            if not isinstance(data, dict):
                continue
            sanitized = sanitize_preset_for_export(
                data,
                blank_api_key=options.get("blankApiKey", False),
                randomize_location=options.get("randomizeLocation", False),
            )
            sanitized_presets[filename] = sanitized
            asset_maps.append(collect_assets_from_preset(sanitized))

        assets = merge_asset_maps(*asset_maps)
        package_meta = {
            "version": PACKAGE_VERSION,
            "packageType": "full",
            "exportedAt": utc_now_iso(),
            "exportOptions": options,
            "presetCount": len(sanitized_presets),
        }

        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(PACKAGE_MANIFEST, json.dumps(package_meta, indent=2))
            archive.writestr(
                f"presets/{MANIFEST_NAME}",
                json.dumps(manifest, indent=2),
            )
            if slideshow is not None:
                archive.writestr(
                    f"presets/{SLIDESHOW_FILE}",
                    json.dumps(slideshow, indent=2),
                )
            for filename, data in sanitized_presets.items():
                archive.writestr(
                    f"presets/{filename}",
                    json.dumps(data, indent=2),
                )
            included, missing = self._write_assets_to_zip(archive, assets)
            if missing:
                package_meta["missingAssets"] = missing
            package_meta["includedAssets"] = included
            archive.writestr(PACKAGE_MANIFEST, json.dumps(package_meta, indent=2))

        stamp = utc_now_iso().replace(":", "").replace("+00:00", "Z")
        download_name = f"mt17-full-backup-{stamp}.zip"
        buffer.seek(0)
        return buffer, download_name

    def _stage_assets_from_zip(
        self,
        archive: zipfile.ZipFile,
        staging_root: Path,
    ) -> list[str]:
        staged: list[str] = []
        for member in archive.namelist():
            normalized = normalize_zip_member(member)
            if not is_safe_zip_member(normalized):
                continue
            top = normalized.split("/", 1)[0]
            if top not in ASSET_FOLDERS:
                continue
            destination = staging_root / Path(normalized)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, destination.open("wb") as target:
                shutil.copyfileobj(source, target)
            staged.append(normalized)
        return staged

    def _commit_staged_assets(self, staging_root: Path, members: list[str]) -> list[str]:
        installed: list[str] = []
        for normalized in members:
            source = staging_root / Path(normalized)
            destination = self.wallpaper_path / Path(normalized)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            installed.append(normalized)
        return installed

    def _validate_archive_limits(self, archive: zipfile.ZipFile) -> None:
        members = archive.infolist()
        if len(members) > MAX_ZIP_MEMBERS:
            raise ValueError(f"ZIP contains too many files (maximum {MAX_ZIP_MEMBERS})")
        total_size = 0
        for member in members:
            normalized = normalize_zip_member(member.filename)
            if not is_safe_zip_member(normalized):
                raise ValueError("ZIP contains unsafe file paths")
            if member.file_size > MAX_ZIP_MEMBER_BYTES:
                raise ValueError(
                    f"ZIP member is too large (maximum {MAX_ZIP_MEMBER_BYTES} bytes)"
                )
            total_size += member.file_size
            if total_size > MAX_ZIP_UNCOMPRESSED_BYTES:
                raise ValueError(
                    "ZIP contains too much uncompressed data "
                    f"(maximum {MAX_ZIP_UNCOMPRESSED_BYTES} bytes)"
                )

    def _read_package_meta(self, archive: zipfile.ZipFile) -> dict:
        try:
            with archive.open(PACKAGE_MANIFEST) as handle:
                meta = json.load(handle)
            if isinstance(meta, dict):
                return meta
        except (KeyError, json.JSONDecodeError):
            pass
        return {"version": 1, "packageType": "unknown"}

    def _load_presets_from_zip(self, archive: zipfile.ZipFile) -> tuple[dict, dict[str, dict], dict | None]:
        manifest: dict = {"version": 1, "presets": []}
        presets: dict[str, dict] = {}
        slideshow: dict | None = None
        normalized_names = {
            normalize_zip_member(name): name for name in archive.namelist()
        }

        manifest_key = f"presets/{MANIFEST_NAME}"
        if manifest_key in normalized_names:
            with archive.open(normalized_names[manifest_key]) as handle:
                loaded = json.load(handle)
            if isinstance(loaded, dict):
                manifest = loaded

        slideshow_key = f"presets/{SLIDESHOW_FILE}"
        if slideshow_key in normalized_names:
            with archive.open(normalized_names[slideshow_key]) as handle:
                loaded = json.load(handle)
            if isinstance(loaded, dict):
                slideshow = loaded

        for normalized, original in normalized_names.items():
            if not normalized.endswith(PRESET_SUFFIX):
                continue
            if not (
                normalized.startswith("presets/")
                or "/" not in normalized
            ):
                continue
            if not is_safe_zip_member(normalized):
                continue
            filename = Path(normalized).name
            if filename in presets:
                continue
            with archive.open(original) as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                presets[filename] = data

        return manifest, presets, slideshow

    def import_zip(
        self,
        zip_bytes: bytes,
        *,
        preset_name: str | None = None,
        import_callback,
        restore_bundle_callback,
        write_slideshow_callback=None,
        allowed_mode: str = "auto",
    ) -> dict:
        if not isinstance(zip_bytes, (bytes, bytearray)) or len(zip_bytes) > MAX_UPLOAD_BYTES:
            raise ValueError(f"ZIP upload is too large (maximum {MAX_UPLOAD_BYTES} bytes)")

        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = Path(temp_dir) / "import.zip"
            zip_path.write_bytes(zip_bytes)

            with zipfile.ZipFile(zip_path, "r") as archive:
                self._validate_archive_limits(archive)

                package_meta = self._read_package_meta(archive)
                try:
                    manifest, presets, slideshow = self._load_presets_from_zip(archive)
                except json.JSONDecodeError as error:
                    raise ValueError("ZIP contains invalid JSON") from error
                if not presets:
                    raise ValueError(
                        "No preset files found in ZIP. Expected presets/*.preset.json"
                    )

                package_type = str(package_meta.get("packageType", "")).lower()
                preset_count = len(presets)
                is_full_package = package_type == "full" or preset_count > 1

                if allowed_mode == "single" and is_full_package:
                    raise ValueError(
                        "That ZIP is a full backup with multiple presets. "
                        "Use Upload full backup ZIP instead."
                    )
                if allowed_mode == "full" and not is_full_package:
                    raise ValueError(
                        "That ZIP contains only one preset. Use Upload preset ZIP instead."
                    )

                asset_stage = Path(temp_dir) / "assets"
                staged_assets = self._stage_assets_from_zip(archive, asset_stage)

                if allowed_mode == "single" or (
                    allowed_mode == "auto" and not is_full_package
                ):
                    preferred = package_meta.get("presetFile")
                    if preferred in presets:
                        filename, data = preferred, presets[preferred]
                    else:
                        filename, data = next(iter(presets.items()))
                    manifest_entry = next(
                        (
                            item
                            for item in manifest.get("presets", [])
                            if isinstance(item, dict) and item.get("file") == filename
                        ),
                        None,
                    )
                    resolved_name = preset_name_from_package(
                        package_meta, manifest_entry, filename
                    )
                    resolved_filename = preset_filename_from_package(
                        package_meta, manifest_entry, filename
                    )
                    entry = import_callback(data, resolved_name, resolved_filename)
                    installed_assets = self._commit_staged_assets(
                        asset_stage, staged_assets
                    )
                    return {
                        "packageType": "single",
                        "preset": entry,
                        "installedAssets": installed_assets,
                        "wallpaperPath": str(self.wallpaper_path),
                        "exportOptions": package_meta.get("exportOptions", {}),
                    }

                count = restore_bundle_callback(
                    {"manifest": manifest, "presets": presets},
                )
                slideshow_saved = False
                if slideshow is not None and write_slideshow_callback is not None:
                    write_slideshow_callback(slideshow)
                    slideshow_saved = True
                installed_assets = self._commit_staged_assets(
                    asset_stage, staged_assets
                )

                return {
                    "packageType": "full",
                    "restoredPresets": count,
                    "slideshowRestored": slideshow_saved,
                    "installedAssets": installed_assets,
                    "wallpaperPath": str(self.wallpaper_path),
                    "exportOptions": package_meta.get("exportOptions", {}),
                }
