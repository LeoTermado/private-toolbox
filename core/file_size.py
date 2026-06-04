"""Shared file-size helpers (no Flask, no I/O beyond stat).

Generic utilities for reading, formatting and comparing file sizes. Used by the
PDF Compressor and reusable by any tool that reports size results (image
resizer, ZIP splitter, archive inspector, media converter, download displays, …).

Low-level functions operate on byte counts (ints) so they can be used without
touching the filesystem; the *_files / compare_files helpers take paths.
"""
import os

_UNITS = ["B", "KB", "MB", "GB", "TB", "PB"]


def get_file_size(path):
    """Return the size of the file at `path` in bytes."""
    return os.path.getsize(path)


def format_file_size(num_bytes, decimals=1):
    """Format a byte count as a human-readable string, e.g. 1536 -> '1.5 KB'.

    Bytes are shown as whole numbers; larger units use `decimals` places.
    Negative values (e.g. a size increase expressed as negative savings) keep
    their sign.
    """
    if num_bytes is None:
        return "0 B"

    size = float(num_bytes)
    sign = "-" if size < 0 else ""
    size = abs(size)

    i = 0
    while size >= 1024 and i < len(_UNITS) - 1:
        size /= 1024.0
        i += 1

    if i == 0:
        return f"{sign}{int(size)} {_UNITS[i]}"
    return f"{sign}{size:.{decimals}f} {_UNITS[i]}"


def size_reduction(original_bytes, output_bytes):
    """Bytes saved going from original to output (negative if output is larger)."""
    return original_bytes - output_bytes


def reduction_ratio(original_bytes, output_bytes):
    """Fraction of size saved (0.0–1.0); negative if output grew. 0.0 if original is 0."""
    if not original_bytes:
        return 0.0
    return (original_bytes - output_bytes) / original_bytes


def reduction_percent(original_bytes, output_bytes):
    """Percentage of size saved (e.g. 42.5). Negative if output grew."""
    return reduction_ratio(original_bytes, output_bytes) * 100.0


def output_is_smaller(original_bytes, output_bytes):
    """True if the output is strictly smaller than the original."""
    return output_bytes < original_bytes


def compare_files(original_path, output_path, decimals=1):
    """Compare two files on disk and return a display-ready dict.

    Keys: original_bytes, output_bytes, original_human, output_human,
    saved_bytes, saved_human, saved_percent, smaller.
    """
    original_bytes = get_file_size(original_path)
    output_bytes = get_file_size(output_path)
    saved = size_reduction(original_bytes, output_bytes)
    return {
        "original_bytes": original_bytes,
        "output_bytes": output_bytes,
        "original_human": format_file_size(original_bytes, decimals),
        "output_human": format_file_size(output_bytes, decimals),
        "saved_bytes": saved,
        "saved_human": format_file_size(saved, decimals),
        "saved_percent": round(reduction_percent(original_bytes, output_bytes), 1),
        "smaller": output_is_smaller(original_bytes, output_bytes),
    }
