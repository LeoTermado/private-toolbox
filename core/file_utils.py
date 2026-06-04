"""Backwards-compatibility wrapper.

The path/folder logic now lives in core.paths and the archive logic in
core.archive. This module re-exports the original names so existing imports
(app.py, the tool services and routes) keep working unchanged.
"""
from core.paths import (
    BASE_DIR,
    INPUT_FOLDER,
    OUTPUT_FOLDER,
    OLD_FOLDER,
    ensure_base_folders,
)
from core.archive import archive_session


def ensure_folders():
    """Compatibility alias for core.paths.ensure_base_folders()."""
    ensure_base_folders()


__all__ = [
    "BASE_DIR",
    "INPUT_FOLDER",
    "OUTPUT_FOLDER",
    "OLD_FOLDER",
    "ensure_folders",
    "archive_session",
]
