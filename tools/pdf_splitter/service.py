"""PDF splitting logic (no Flask).

Thin tool layer over the shared core helpers (core.paths, core.uploads,
core.pdf_utils). The web layer in routes.py only handles request/response.
"""
from core.paths import tool_input_dir, tool_output_dir, ensure_tool_folders
from core.uploads import save_upload as _save_upload
from core.pdf_utils import split_pdf_by_ranges
from core.archive_utils import zip_files_to_buffer

TOOL_SLUG = "pdf_splitter"

# Splitter keeps its files in dedicated subfolders (input/pdf_splitter, output/pdf_splitter).
SPLITTER_INPUT = tool_input_dir(TOOL_SLUG)
SPLITTER_OUTPUT = tool_output_dir(TOOL_SLUG)


def ensure_splitter_folders():
    """Create input/pdf_splitter/ and output/pdf_splitter/ if they don't exist."""
    return ensure_tool_folders(TOOL_SLUG)


def save_upload(file_storage):
    """Save a Werkzeug uploaded file into input/pdf_splitter/ and return its path."""
    ensure_splitter_folders()
    return _save_upload(file_storage, SPLITTER_INPUT)


def split_pdf(input_path, range_string):
    """Split the PDF at input_path according to range_string (e.g. '1-10, 15').

    Writes one PDF per range part into output/pdf_splitter/ and returns the list
    of created file paths. Files persist until archived.
    """
    ensure_splitter_folders()
    return split_pdf_by_ranges(input_path, range_string, SPLITTER_OUTPUT)


def build_zip(created_files):
    """Bundle the created split files into an in-memory ZIP and return it."""
    return zip_files_to_buffer(created_files)
