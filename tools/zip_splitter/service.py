"""ZIP Splitter logic (no Flask).

Splits one uploaded ZIP into several smaller ZIP "parts", grouping whole entries
so each part stays under a size limit. Whole files are never split across parts.
Standard library only.
"""
import os
import zipfile

from core.paths import tool_input_dir, tool_output_dir, ensure_tool_folders
from core.uploads import save_upload as _save_upload
from core.filenames import unique_path
from core.archive_utils import zip_files_to_path

TOOL_SLUG = "zip_splitter"

ZIP_INPUT = tool_input_dir(TOOL_SLUG)
ZIP_OUTPUT = tool_output_dir(TOOL_SLUG)

ALLOWED_EXTENSIONS = {".zip"}
DEFAULT_MAX_MB = 10


def ensure_zip_folders():
    return ensure_tool_folders(TOOL_SLUG)


def save_upload(file_storage):
    ensure_zip_folders()
    return _save_upload(file_storage, ZIP_INPUT, default_name="archive.zip")


def clamp_max_mb(value):
    try:
        n = int(value)
    except (TypeError, ValueError):
        return DEFAULT_MAX_MB
    return max(1, min(2048, n))


def split_zip(input_path, max_mb):
    """Split the ZIP at input_path into parts under max_mb (uncompressed) each.

    Returns (part_infos, bundle_path) where part_infos is a list of
    {name, file_count, size_bytes}. Raises ValueError if not a valid/non-empty ZIP.
    """
    if not zipfile.is_zipfile(input_path):
        raise ValueError("This file is not a valid ZIP archive.")

    ensure_zip_folders()
    limit = max_mb * 1024 * 1024

    # Greedy bin-packing of whole entries by uncompressed size.
    groups = []
    current = []
    current_size = 0
    with zipfile.ZipFile(input_path) as zin:
        members = [i for i in zin.infolist() if not i.is_dir()]
        if not members:
            raise ValueError("This ZIP has no files to split.")
        for info in members:
            data = zin.read(info)
            size = len(data)
            if current and current_size + size > limit:
                groups.append(current)
                current = []
                current_size = 0
            current.append((info.filename, data))
            current_size += size
        if current:
            groups.append(current)

    part_paths = []
    part_infos = []
    for idx, group in enumerate(groups, start=1):
        part_path = unique_path(ZIP_OUTPUT, f"part_{idx:03d}.zip")
        with zipfile.ZipFile(part_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for name, data in group:
                zout.writestr(name, data)
        part_paths.append(part_path)
        part_infos.append({
            "name": os.path.basename(part_path),
            "file_count": len(group),
            "size_bytes": os.path.getsize(part_path),
        })

    bundle_path = zip_files_to_path(part_paths, unique_path(ZIP_OUTPUT, "zip_parts.zip"))
    return part_infos, bundle_path
