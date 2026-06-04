"""Generic ZIP archive-file helpers (no Flask).

Different from core.archive: that module archives the whole app workspace into
old/. This module builds actual ZIP archive files from a list of source files,
so any tool that produces several output files can bundle them for download.

Note: only ZIP creation is provided here. Archive inspection/extraction is not
implemented yet.
"""
import os
import zipfile
from io import BytesIO


def _default_arcname(file_path):
    """Default name used inside the ZIP for a given source path."""
    return os.path.basename(file_path)


def zip_files_to_buffer(file_paths, arcname_func=None):
    """Create an in-memory ZIP (BytesIO) of the given files, preserving order.

    arcname_func(file_path) -> name inside the archive. Defaults to the file's
    basename.
    """
    arcname_func = arcname_func or _default_arcname
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zipf:
        for path in file_paths:
            zipf.write(path, arcname_func(path))
    buffer.seek(0)
    return buffer


def zip_files_to_path(file_paths, output_path, arcname_func=None):
    """Create a ZIP file on disk of the given files, preserving order.

    Returns output_path. arcname_func behaves as in zip_files_to_buffer().
    """
    arcname_func = arcname_func or _default_arcname
    with zipfile.ZipFile(output_path, 'w') as zipf:
        for path in file_paths:
            zipf.write(path, arcname_func(path))
    return output_path
