"""PDF Password Guard logic (no Flask).

Add or remove a PDF open-password using PyPDF2's standard PDF encryption
(RC4 128-bit). This deters casual access; it is NOT strong modern encryption.
The UI states this honestly.
"""
import os

from PyPDF2 import PdfReader, PdfWriter

from core.paths import tool_input_dir, tool_output_dir, ensure_tool_folders
from core.uploads import save_upload as _save_upload
from core.filenames import sanitize_filename, unique_path

TOOL_SLUG = "pdf_password_guard"

GUARD_INPUT = tool_input_dir(TOOL_SLUG)
GUARD_OUTPUT = tool_output_dir(TOOL_SLUG)

MODE_CHOICES = [
    ("protect", "Protect — add a password"),
    ("unlock", "Unlock — remove a known password"),
]
DEFAULT_MODE = "protect"


class GuardError(Exception):
    """User-facing error (wrong password, already encrypted, etc.)."""


def ensure_guard_folders():
    return ensure_tool_folders(TOOL_SLUG)


def save_upload(file_storage):
    ensure_guard_folders()
    return _save_upload(file_storage, GUARD_INPUT, default_name="document.pdf")


def _output_path(input_path, suffix):
    stem = os.path.splitext(os.path.basename(input_path))[0]
    stem = sanitize_filename(stem, default="document")
    return unique_path(GUARD_OUTPUT, f"{stem}_{suffix}.pdf")


def protect(input_path, password):
    """Write a password-protected copy; return its path. Raises GuardError."""
    ensure_guard_folders()
    try:
        reader = PdfReader(input_path)
    except Exception:
        raise GuardError("Could not read this PDF. It may be corrupt.")

    if reader.is_encrypted:
        raise GuardError("This PDF is already password-protected. Unlock it first.")

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(password)  # standard PDF encryption (RC4-128)

    out_path = _output_path(input_path, "protected")
    with open(out_path, "wb") as f:
        writer.write(f)
    return out_path


def unlock(input_path, password):
    """Write a copy with the password removed; return its path. Raises GuardError."""
    ensure_guard_folders()
    try:
        reader = PdfReader(input_path)
    except Exception:
        raise GuardError("Could not read this PDF. It may be corrupt.")

    if not reader.is_encrypted:
        raise GuardError("This PDF is not password-protected.")

    try:
        ok = reader.decrypt(password)
    except Exception:
        # e.g. AES-encrypted PDFs that this PyPDF2 build can't open.
        raise GuardError("Wrong password, or this PDF uses unsupported encryption.")
    if not ok:
        raise GuardError("Wrong password for this PDF.")

    writer = PdfWriter()
    try:
        for page in reader.pages:
            writer.add_page(page)
    except Exception:
        raise GuardError("Could not read the PDF after unlocking. It may use unsupported encryption.")

    out_path = _output_path(input_path, "unlocked")
    with open(out_path, "wb") as f:
        writer.write(f)
    return out_path
