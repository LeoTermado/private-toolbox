"""PDF merging logic (no Flask).

Thin tool layer over the shared core helpers (core.paths, core.filenames,
core.uploads, core.pdf_utils). Uses its own subfolders under input/ and output/
so it never interferes with the PDF Splitter.
"""
from core.paths import tool_input_dir, tool_output_dir, ensure_tool_folders
from core.filenames import sanitize_output_filename, unique_path  # noqa: F401 (re-exported for routes)
from core.uploads import save_uploads as _save_uploads
from core.pdf_utils import merge_pdfs  # noqa: F401 (re-exported for routes)

TOOL_SLUG = "pdf_merger"

# Merger keeps its files in dedicated subfolders.
MERGER_INPUT = tool_input_dir(TOOL_SLUG)
MERGER_OUTPUT = tool_output_dir(TOOL_SLUG)


def ensure_merger_folders():
    """Create input/pdf_merger/ and output/pdf_merger/ if they don't exist."""
    return ensure_tool_folders(TOOL_SLUG)


def sanitize_output_name(raw_name):
    """Return a safe '<name>.pdf' filename, or None if nothing usable remains."""
    return sanitize_output_filename(raw_name, ".pdf")


def save_uploads(file_storages):
    """Save each uploaded PDF into input/pdf_merger/ and return their paths in order.

    Filenames are sanitized and de-duplicated so two uploads with the same name
    don't clobber each other. Order is preserved.
    """
    ensure_merger_folders()
    return _save_uploads(file_storages, MERGER_INPUT, default_name="upload.pdf")
