"""PDF splitting logic (no Flask).

Extracted from the original app.py `split_pdf_web` route so the web layer only
handles the request/response and this module does the actual work.
"""
import os
import zipfile
from io import BytesIO

from PyPDF2 import PdfReader, PdfWriter

from core.file_utils import INPUT_FOLDER, OUTPUT_FOLDER
from core.page_range_parser import parse_single_range

# Splitter keeps its files in dedicated subfolders (mirrors the PDF Merger).
SPLITTER_INPUT = os.path.join(INPUT_FOLDER, 'pdf_splitter')
SPLITTER_OUTPUT = os.path.join(OUTPUT_FOLDER, 'pdf_splitter')


def ensure_splitter_folders():
    """Create input/pdf_splitter/ and output/pdf_splitter/ if they don't exist."""
    os.makedirs(SPLITTER_INPUT, exist_ok=True)
    os.makedirs(SPLITTER_OUTPUT, exist_ok=True)


def save_upload(file_storage):
    """Save a Werkzeug uploaded file into input/pdf_splitter/ and return its path."""
    ensure_splitter_folders()
    input_path = os.path.join(SPLITTER_INPUT, file_storage.filename)
    file_storage.save(input_path)
    return input_path


def split_pdf(input_path, range_string):
    """Split the PDF at input_path according to range_string (e.g. '1-10, 15').

    Writes one PDF per range part into output/ and returns the list of created
    file paths. Files persist in output/ until archived.
    """
    ensure_splitter_folders()
    reader = PdfReader(input_path)
    total_pages = len(reader.pages)

    created_files = []
    for part in range_string.split(","):
        part = part.strip()
        if not part:
            continue

        try:
            target_pages = parse_single_range(part, total_pages)
        except ValueError:
            continue

        if not target_pages:
            continue

        writer = PdfWriter()
        for page_num in target_pages:
            writer.add_page(reader.pages[page_num])

        output_filename = os.path.join(SPLITTER_OUTPUT, f"{part}.pdf")
        with open(output_filename, "wb") as out_file:
            writer.write(out_file)
        created_files.append(output_filename)

    return created_files


def build_zip(created_files):
    """Bundle the created split files into an in-memory ZIP and return it."""
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w') as zipf:
        for f in created_files:
            zipf.write(f, os.path.basename(f))

    zip_buffer.seek(0)
    return zip_buffer
