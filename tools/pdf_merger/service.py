"""PDF merging logic (no Flask).

Combines multiple uploaded PDFs into one, in the order given. Mirrors the
structure of tools/pdf_splitter/service.py. Uses its own subfolders under
input/ and output/ so it never interferes with the PDF Splitter.
"""
import os

from PyPDF2 import PdfReader, PdfWriter
from werkzeug.utils import secure_filename

from core.file_utils import INPUT_FOLDER, OUTPUT_FOLDER

# Merger keeps its files in dedicated subfolders.
MERGER_INPUT = os.path.join(INPUT_FOLDER, 'pdf_merger')
MERGER_OUTPUT = os.path.join(OUTPUT_FOLDER, 'pdf_merger')


def ensure_merger_folders():
    """Create input/pdf_merger/ and output/pdf_merger/ if they don't exist."""
    os.makedirs(MERGER_INPUT, exist_ok=True)
    os.makedirs(MERGER_OUTPUT, exist_ok=True)


def sanitize_output_name(raw_name):
    """Return a safe '<name>.pdf' filename, or None if nothing usable remains.

    secure_filename strips directory components and unsafe characters, which
    also prevents path traversal (e.g. '../../evil').
    """
    if not raw_name:
        return None

    safe = secure_filename(raw_name.strip())
    if not safe:
        return None

    if not safe.lower().endswith('.pdf'):
        safe += '.pdf'
    return safe


def unique_path(folder, filename):
    """Return a path in folder that doesn't exist yet.

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


def save_uploads(file_storages):
    """Save each uploaded PDF into input/pdf_merger/ and return their paths in order.

    Filenames are sanitized and de-duplicated so two uploads with the same name
    don't clobber each other.
    """
    ensure_merger_folders()
    saved_paths = []
    for fs in file_storages:
        safe_name = secure_filename(fs.filename) or "upload.pdf"
        if not safe_name.lower().endswith('.pdf'):
            safe_name += '.pdf'
        dest = unique_path(MERGER_INPUT, safe_name)
        fs.save(dest)
        saved_paths.append(dest)
    return saved_paths


def merge_pdfs(input_paths: list[str], output_path: str) -> str:
    """Merge the PDFs at input_paths (in order) into a single PDF at output_path.

    Reads every source PDF, appends all of its pages, writes the result, and
    returns output_path. Source files are only read, never modified.
    """
    writer = PdfWriter()
    for path in input_paths:
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)

    with open(output_path, "wb") as out_file:
        writer.write(out_file)

    return output_path
