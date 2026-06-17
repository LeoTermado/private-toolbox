"""Archive Content Inspector logic (no Flask).

Read-only inspection of ZIP and TAR archives using the standard library. Lists
entries with sizes and modified dates and summarizes totals/compression ratio.
"""
import os
import tarfile
import zipfile
from datetime import datetime

from core.paths import tool_input_dir, tool_output_dir, ensure_tool_folders
from core.uploads import save_upload as _save_upload

TOOL_SLUG = "archive_content_inspector"

INSPECTOR_INPUT = tool_input_dir(TOOL_SLUG)
INSPECTOR_OUTPUT = tool_output_dir(TOOL_SLUG)

# Last-extension based check; .tar.gz/.tgz/.tar.bz2 etc. are detected by content.
ALLOWED_EXTENSIONS = {".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz"}

# Cap rows rendered so a huge archive can't produce an enormous page.
MAX_ENTRIES = 1000


def ensure_inspector_folders():
    """Create input/archive_content_inspector/ and output/... if missing."""
    return ensure_tool_folders(TOOL_SLUG)


def save_upload(file_storage):
    """Save the uploaded archive into input/archive_content_inspector/."""
    ensure_inspector_folders()
    return _save_upload(file_storage, INSPECTOR_INPUT, default_name="archive.zip")


def _safe_dt(dt_tuple=None, timestamp=None):
    try:
        if dt_tuple is not None:
            return datetime(*dt_tuple[:6]).strftime("%Y-%m-%d %H:%M")
        if timestamp:
            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
    except (ValueError, OSError, TypeError):
        return ""
    return ""


def inspect_archive(path):
    """Inspect a ZIP or TAR archive; return a summary dict.

    Raises ValueError if the file is not a readable ZIP or TAR archive.
    """
    if zipfile.is_zipfile(path):
        return _inspect_zip(path)
    if tarfile.is_tarfile(path):
        return _inspect_tar(path)
    raise ValueError("This file is not a readable ZIP or TAR archive.")


def _inspect_zip(path):
    entries = []
    total = 0
    compressed = 0
    with zipfile.ZipFile(path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            total += info.file_size
            compressed += info.compress_size
            entries.append({
                "name": info.filename,
                "size": info.file_size,
                "compressed": info.compress_size,
                "modified": _safe_dt(dt_tuple=info.date_time),
            })
    return _summary("ZIP", entries, total, compressed)


def _inspect_tar(path):
    entries = []
    total = 0
    with tarfile.open(path) as tf:
        for member in tf.getmembers():
            if not member.isfile():
                continue
            total += member.size
            entries.append({
                "name": member.name,
                "size": member.size,
                "compressed": None,  # tar members have no per-entry compressed size
                "modified": _safe_dt(timestamp=member.mtime),
            })
    return _summary("TAR", entries, total, None)


def _summary(kind, entries, total, compressed):
    ratio = None
    if compressed and total:
        ratio = round((1 - compressed / total) * 100, 1)
    return {
        "type": kind,
        "entries": entries,
        "file_count": len(entries),
        "total_bytes": total,
        "compressed_bytes": compressed,
        "ratio": ratio,
    }
