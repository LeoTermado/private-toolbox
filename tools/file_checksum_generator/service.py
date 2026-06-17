"""File Checksum Generator logic (no Flask).

Computes cryptographic hashes for uploaded files using the standard library
hashlib, and writes a plain-text report.
"""
import hashlib
import os

from core.paths import tool_input_dir, tool_output_dir, ensure_tool_folders
from core.uploads import save_uploads as _save_uploads
from core.filenames import unique_path

TOOL_SLUG = "file_checksum_generator"

CHECKSUM_INPUT = tool_input_dir(TOOL_SLUG)
CHECKSUM_OUTPUT = tool_output_dir(TOOL_SLUG)

# Algorithms offered in the UI (all from hashlib, no extra deps).
ALGORITHMS = ["md5", "sha1", "sha256", "sha512"]
DEFAULT_ALGORITHMS = ["sha256"]

_CHUNK = 65536


def ensure_checksum_folders():
    return ensure_tool_folders(TOOL_SLUG)


def save_uploads(file_storages):
    """Save uploads into input/file_checksum_generator/ and return their paths."""
    ensure_checksum_folders()
    return _save_uploads(file_storages, CHECKSUM_INPUT, default_name="file")


def normalize_algorithms(algos):
    """Keep only supported algorithms (in canonical order); fall back to default."""
    chosen = [a for a in ALGORITHMS if a in set(algos or [])]
    return chosen or list(DEFAULT_ALGORITHMS)


def compute_checksums(path, algos):
    """Return {algorithm: hexdigest} for the file at path (single streamed read)."""
    hashers = {a: hashlib.new(a) for a in algos}
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK), b""):
            for h in hashers.values():
                h.update(chunk)
    return {a: hashers[a].hexdigest() for a in algos}


def write_report(rows, algos):
    """Write a plain-text checksum report and return its path.

    rows: [{"name": str, "size_human": str, "hashes": {algo: hex}}]
    """
    ensure_checksum_folders()
    out_path = unique_path(CHECKSUM_OUTPUT, "checksums.txt")
    lines = []
    for row in rows:
        lines.append(f"{row['name']}  ({row['size_human']})")
        for algo in algos:
            lines.append(f"  {algo}: {row['hashes'][algo]}")
        lines.append("")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return out_path
