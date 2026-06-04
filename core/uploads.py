"""Helpers for saving Flask FileStorage uploads to disk.

This module only saves files. It does NOT validate extensions, flash messages,
or build responses — callers are responsible for validation and for ensuring
the destination folder exists.

Duplicate handling (when unique=True): if a file with the same sanitized name
already exists AND its content is identical to the upload, the existing path is
reused instead of writing file_2.pdf, file_3.pdf, ... If the name collides but
the content differs, a new unique name is used so nothing is overwritten.
"""
import hashlib
import os

from core.filenames import sanitize_filename, unique_path

_CHUNK_SIZE = 65536


def hash_file(path, chunk_size=_CHUNK_SIZE):
    """Return the SHA-256 hex digest of the file at `path`."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_filestorage(file_storage, chunk_size=_CHUNK_SIZE):
    """Return the SHA-256 hex digest of an upload's content.

    Reads the stream from the start and resets it back to 0 afterwards so the
    upload can still be saved normally.
    """
    stream = file_storage.stream
    stream.seek(0)
    h = hashlib.sha256()
    for chunk in iter(lambda: stream.read(chunk_size), b""):
        h.update(chunk)
    stream.seek(0)
    return h.hexdigest()


def _filestorage_size(file_storage):
    """Return the byte size of an upload, leaving the stream rewound to 0."""
    stream = file_storage.stream
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(0)
    return size


def files_are_identical(existing_path, file_storage):
    """True if the file at existing_path has the same content as the upload.

    Compares size first (cheap) and only hashes when sizes match.
    """
    if _filestorage_size(file_storage) != os.path.getsize(existing_path):
        return False
    return hash_file(existing_path) == hash_filestorage(file_storage)


def find_reusable_upload_path(file_storage, destination_folder, sanitized_filename):
    """Return an existing identical file's path to reuse, or None to save anew.

    Only checks the exact sanitized filename in the destination folder.
    """
    candidate = os.path.join(destination_folder, sanitized_filename)
    if os.path.exists(candidate) and files_are_identical(candidate, file_storage):
        return candidate
    return None


def save_upload(file_storage, destination_folder, filename=None, sanitize=True,
                unique=True, default_name="upload"):
    """Save a single upload into destination_folder and return the saved path.

    - filename: override the stored name (defaults to the upload's own name).
    - sanitize: run the name through core.filenames.sanitize_filename.
    - unique: avoid overwriting via core.filenames.unique_path (file_2.pdf, ...).
      When the same name already exists with identical content, the existing
      path is reused instead of creating a duplicate copy.
    - default_name: used when the name is empty/unusable.
    """
    name = filename if filename is not None else file_storage.filename

    if sanitize:
        name = sanitize_filename(name, default=default_name)
    elif not name:
        name = default_name

    if unique:
        # Reuse an identical, same-named file if one is already saved.
        reusable = find_reusable_upload_path(file_storage, destination_folder, name)
        if reusable is not None:
            return reusable
        dest = unique_path(destination_folder, name)
    else:
        dest = os.path.join(destination_folder, name)

    # Hashing/size checks above may have moved the stream pointer; rewind so the
    # full content is written.
    try:
        file_storage.stream.seek(0)
    except (AttributeError, ValueError, OSError):
        pass

    file_storage.save(dest)
    return dest


def save_uploads(file_storages, destination_folder, sanitize=True, unique=True,
                 default_name="upload"):
    """Save many uploads in order and return their saved paths (order preserved)."""
    saved_paths = []
    for fs in file_storages:
        saved_paths.append(
            save_upload(fs, destination_folder, sanitize=sanitize, unique=unique,
                        default_name=default_name)
        )
    return saved_paths
