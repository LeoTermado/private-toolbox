"""PDF Compressor logic (no Flask).

Thin tool layer over the shared core helpers (core.paths, core.filenames,
core.uploads, core.pdf_utils). Uses its own subfolders under input/ and output/
so it never interferes with the other tools.
"""
import os

from core.paths import tool_input_dir, tool_output_dir, ensure_tool_folders
from core.filenames import sanitize_filename, sanitize_output_filename, unique_path
from core.uploads import save_upload as _save_upload
from core.pdf_utils import compress_pdf, ghostscript_command

TOOL_SLUG = "pdf_compressor"

# Compressor keeps its files in dedicated subfolders.
COMPRESSOR_INPUT = tool_input_dir(TOOL_SLUG)
COMPRESSOR_OUTPUT = tool_output_dir(TOOL_SLUG)

# User-facing compression levels -> Ghostscript quality presets supported by
# core.pdf_utils. Ordered low -> high compression.
LEVEL_CHOICES = [
    ("low", "Low compression / best quality"),
    ("medium", "Medium compression / balanced"),
    ("high", "High compression / smallest file"),
]
_LEVEL_TO_QUALITY = {
    "low": "printer",   # best quality, least shrink
    "medium": "ebook",  # balanced (default)
    "high": "screen",   # smallest file, most shrink
}
DEFAULT_LEVEL = "medium"


def ensure_compressor_folders():
    """Create input/pdf_compressor/ and output/pdf_compressor/ if they don't exist."""
    return ensure_tool_folders(TOOL_SLUG)


def ghostscript_status():
    """Return whether Ghostscript is available and which command was found.

    Reuses core.pdf_utils.ghostscript_command() — no duplicated detection logic.
    """
    cmd = ghostscript_command()
    return {"available": cmd is not None, "command": cmd}


def resolve_quality(level):
    """Map a UI level to a core.pdf_utils quality preset (falls back to default)."""
    return _LEVEL_TO_QUALITY.get(level, _LEVEL_TO_QUALITY[DEFAULT_LEVEL])


def save_upload(file_storage):
    """Save the uploaded PDF into input/pdf_compressor/ and return its path."""
    ensure_compressor_folders()
    return _save_upload(file_storage, COMPRESSOR_INPUT, default_name="document.pdf")


def build_output_name(raw_name, input_path):
    """Return a safe '<name>.pdf'.

    If the user supplied a name, sanitize it. Otherwise derive it from the input
    filename as '<stem>_compressed.pdf'.
    """
    safe = sanitize_output_filename(raw_name, ".pdf")
    if safe:
        return safe
    stem = os.path.splitext(os.path.basename(input_path))[0]
    stem = sanitize_filename(stem, default="document")
    return f"{stem}_compressed.pdf"


def compress(input_path, output_name, level):
    """Compress input_path into output/pdf_compressor/ and return a CompressionResult.

    Uses engine="auto" (Ghostscript when available, PyPDF2 fallback otherwise).
    The output path is made unique so existing files are never overwritten.
    """
    ensure_compressor_folders()
    output_path = unique_path(COMPRESSOR_OUTPUT, output_name)
    quality = resolve_quality(level)
    return compress_pdf(input_path, output_path, quality=quality, engine="auto")
