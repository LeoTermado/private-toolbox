"""Pure validation helpers.

No Flask, no I/O, no saving, no flashing, no business logic — just simple checks
and filtering that any tool can reuse. Callers decide what to do with the
True/False results (flash, redirect, etc.).
"""
import os


def has_allowed_extension(filename, extensions):
    """True if `filename`'s extension is in `extensions` (case-insensitive).

    `extensions` may contain entries with or without a leading dot, e.g.
    {".pdf"} or {"pdf"}.
    """
    if not filename:
        return False

    ext = os.path.splitext(filename)[1].lower()
    if not ext:
        return False

    normalized = {
        (e.lower() if e.startswith('.') else '.' + e.lower())
        for e in extensions
    }
    return ext in normalized


def is_pdf_filename(filename):
    """Thin PDF-specific wrapper around has_allowed_extension()."""
    return has_allowed_extension(filename, {".pdf"})


def filter_nonempty_uploads(file_storages):
    """Return only uploads that actually carry a file, preserving order."""
    return [f for f in file_storages if f and f.filename]


def validate_upload_count(files, min_count=1, max_count=None):
    """Return True if len(files) is within [min_count, max_count]."""
    count = len(files)
    if count < min_count:
        return False
    if max_count is not None and count > max_count:
        return False
    return True
