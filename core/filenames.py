"""Filename sanitizing and unique-path helpers (no Flask, no PDF).

Centralizes the logic that previously lived in tools/pdf_merger/service.py so
all tools sanitize and de-duplicate filenames the same way.
"""
import os

from werkzeug.utils import secure_filename


def sanitize_filename(raw_name, default=None):
    """Return a filesystem-safe filename, or `default` if nothing usable remains.

    Uses werkzeug.secure_filename, which strips directory components and unsafe
    characters (also prevents path traversal like '../../evil').
    """
    if not raw_name:
        return default

    safe = secure_filename(raw_name.strip())
    if not safe:
        return default
    return safe


def ensure_extension(filename, extension):
    """Append `extension` to `filename` if it isn't already present."""
    if not extension.startswith('.'):
        extension = '.' + extension
    if not filename.lower().endswith(extension.lower()):
        filename += extension
    return filename


def sanitize_output_filename(raw_name, extension=".pdf"):
    """Sanitize a user-provided output name and ensure the extension.

    Returns None if the name sanitizes to nothing usable.
    """
    safe = sanitize_filename(raw_name)
    if safe is None:
        return None
    return ensure_extension(safe, extension)


def unique_path(folder, filename):
    """Return a path in `folder` that doesn't exist yet.

    documents.pdf -> documents_2.pdf -> documents_3.pdf ...
    """
    candidate = os.path.join(folder, filename)
    if not os.path.exists(candidate):
        return candidate

    base, ext = os.path.splitext(filename)
    counter = 2
    while True:
        candidate = os.path.join(folder, f"{base}_{counter}{ext}")
        if not os.path.exists(candidate):
            return candidate
        counter += 1
