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


def save_upload(file_storage):
    """Save a Werkzeug uploaded file into input/ and return its path."""
    input_path = os.path.join(INPUT_FOLDER, file_storage.filename)
    file_storage.save(input_path)
    return input_path


def split_pdf(input_path, range_string):
    """Split the PDF at input_path according to range_string (e.g. '1-10, 15').

    Writes one PDF per range part into output/ and returns the list of created
    file paths. Files persist in output/ until archived.
    """
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

        output_filename = os.path.join(OUTPUT_FOLDER, f"{part}.pdf")
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
