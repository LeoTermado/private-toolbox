"""Shared PyPDF2 helpers for splitting and merging.

Page-range parsing is NOT duplicated here — it is reused from
core.page_range_parser.
"""
import os

from PyPDF2 import PdfReader, PdfWriter

from core.page_range_parser import parse_single_range


def get_page_count(input_path):
    """Return the number of pages in the PDF at input_path."""
    return len(PdfReader(input_path).pages)


def write_pages(input_path, page_indexes, output_path):
    """Write the given zero-based page indexes from input_path to output_path.

    Returns output_path. The source file is only read, never modified.
    """
    reader = PdfReader(input_path)
    writer = PdfWriter()
    for idx in page_indexes:
        writer.add_page(reader.pages[idx])

    with open(output_path, "wb") as out_file:
        writer.write(out_file)

    return output_path


def split_pdf_by_ranges(input_path, range_string, output_folder):
    """Create one PDF per comma-separated range part and return the output paths.

    Each part (e.g. '1-10' or '15') is named '<part>.pdf' in output_folder.
    Empty, invalid, or empty-result parts are skipped — matching the original
    PDF Splitter behavior exactly.
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

        output_filename = os.path.join(output_folder, f"{part}.pdf")
        with open(output_filename, "wb") as out_file:
            writer.write(out_file)
        created_files.append(output_filename)

    return created_files


def merge_pdfs(input_paths, output_path):
    """Merge the PDFs at input_paths (in order) into one PDF at output_path.

    Reads each source PDF, appends all its pages, writes the result, and returns
    output_path. Source files are only read, never modified.
    """
    writer = PdfWriter()
    for path in input_paths:
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)

    with open(output_path, "wb") as out_file:
        writer.write(out_file)

    return output_path
