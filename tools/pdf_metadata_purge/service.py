"""PDF Metadata Purge logic (no Flask).

Reads a PDF's document information and writes a copy with that metadata removed,
using PyPDF2 (already installed).
"""
import os

from PyPDF2 import PdfReader, PdfWriter

from core.paths import tool_input_dir, tool_output_dir, ensure_tool_folders
from core.uploads import save_upload as _save_upload
from core.filenames import sanitize_filename, sanitize_output_filename, unique_path

TOOL_SLUG = "pdf_metadata_purge"

PURGE_INPUT = tool_input_dir(TOOL_SLUG)
PURGE_OUTPUT = tool_output_dir(TOOL_SLUG)

# Human labels for the DocumentInformation fields we surface.
_META_FIELDS = [
    ("title", "Title"),
    ("author", "Author"),
    ("subject", "Subject"),
    ("creator", "Creator"),
    ("producer", "Producer"),
    ("creation_date_raw", "Created"),
    ("modification_date_raw", "Modified"),
]


def ensure_purge_folders():
    return ensure_tool_folders(TOOL_SLUG)


def save_upload(file_storage):
    ensure_purge_folders()
    return _save_upload(file_storage, PURGE_INPUT, default_name="document.pdf")


def read_metadata(reader):
    """Return a list of {label, value} for non-empty metadata fields."""
    meta = reader.metadata
    rows = []
    if not meta:
        return rows
    for attr, label in _META_FIELDS:
        value = getattr(meta, attr, None)
        if value:
            rows.append({"label": label, "value": str(value)})
    return rows


def build_output_name(raw_name, input_path):
    """Return a safe '<name>.pdf' (defaults to '<stem>_clean.pdf')."""
    safe = sanitize_output_filename(raw_name, ".pdf")
    if safe:
        return safe
    stem = os.path.splitext(os.path.basename(input_path))[0]
    stem = sanitize_filename(stem, default="document")
    return f"{stem}_clean.pdf"


def purge_metadata(input_path, output_name):
    """Write a copy of the PDF with document metadata cleared.

    Returns (output_path, original_metadata_rows).
    Raises ValueError if the PDF is encrypted (cannot be processed as-is).
    """
    ensure_purge_folders()
    reader = PdfReader(input_path)
    if reader.is_encrypted:
        raise ValueError("This PDF is password-protected. Remove the password first.")

    original = read_metadata(reader)

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    # Replace the document info dictionary with an empty one.
    writer.add_metadata({})

    output_path = unique_path(PURGE_OUTPUT, output_name)
    with open(output_path, "wb") as out_file:
        writer.write(out_file)

    return output_path, original
