"""File Renamer logic (no Flask).

Batch-renames uploaded files using one of two modes and bundles the results
into a ZIP for download. Stdlib + existing core helpers only.
"""
import os
import shutil

from core.paths import tool_input_dir, tool_output_dir, ensure_tool_folders
from core.uploads import save_uploads as _save_uploads
from core.filenames import sanitize_filename, unique_path
from core.archive_utils import zip_files_to_path

TOOL_SLUG = "file_renamer"

RENAMER_INPUT = tool_input_dir(TOOL_SLUG)
RENAMER_OUTPUT = tool_output_dir(TOOL_SLUG)

MODE_CHOICES = [
    ("sequence", "Sequential numbering (base name + number)"),
    ("prefix_suffix", "Add a prefix and/or suffix to each name"),
]
DEFAULT_MODE = "sequence"


def ensure_renamer_folders():
    return ensure_tool_folders(TOOL_SLUG)


def save_uploads(file_storages):
    ensure_renamer_folders()
    return _save_uploads(file_storages, RENAMER_INPUT, default_name="file")


def plan_names(input_paths, mode, base_name="", prefix="", suffix="", start=1):
    """Return [(input_path, new_filename), ...] preserving order.

    Names are sanitized and de-duplicated within the batch; the original
    extension is always preserved.
    """
    results = []
    used = set()
    count = len(input_paths)
    width = len(str(start + count - 1)) if count else 1

    for i, path in enumerate(input_paths):
        stem, ext = os.path.splitext(os.path.basename(path))

        if mode == "sequence":
            number = str(start + i).zfill(width)
            raw = f"{base_name}_{number}"
        else:  # prefix_suffix
            raw = f"{prefix}{stem}{suffix}"

        safe = sanitize_filename(raw, default=f"file_{i + 1}")
        new_name = f"{safe}{ext}"

        # De-duplicate within this batch (case-insensitive).
        candidate = new_name
        k = 2
        while candidate.lower() in used:
            candidate = f"{safe}_{k}{ext}"
            k += 1
        used.add(candidate.lower())
        results.append((path, candidate))

    return results


def apply_renames(plan):
    """Copy each source to output/ under its new name; return the output paths."""
    ensure_renamer_folders()
    out_paths = []
    for src, new_name in plan:
        dest = unique_path(RENAMER_OUTPUT, new_name)
        shutil.copy2(src, dest)
        out_paths.append(dest)
    return out_paths


def build_zip(out_paths):
    """Bundle the renamed files into a ZIP in output/ and return its path."""
    ensure_renamer_folders()
    zip_path = unique_path(RENAMER_OUTPUT, "renamed_files.zip")
    return zip_files_to_path(out_paths, zip_path)
