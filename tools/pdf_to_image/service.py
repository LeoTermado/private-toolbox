"""PDF to Image logic (no Flask).

Renders each PDF page to an image with PyMuPDF (fitz) and bundles the pages
into a ZIP for download.
"""
import os

import fitz  # PyMuPDF

from core.paths import tool_input_dir, tool_output_dir, ensure_tool_folders
from core.uploads import save_upload as _save_upload
from core.filenames import sanitize_filename, unique_path
from core.archive_utils import zip_files_to_path

TOOL_SLUG = "pdf_to_image"

PDF2IMG_INPUT = tool_input_dir(TOOL_SLUG)
PDF2IMG_OUTPUT = tool_output_dir(TOOL_SLUG)

FORMAT_CHOICES = [("png", "PNG"), ("jpeg", "JPEG")]
_FORMAT_EXT = {"png": "png", "jpeg": "jpg"}
DEFAULT_FORMAT = "png"

DEFAULT_DPI = 150
MIN_DPI = 36
MAX_DPI = 600


class RenderError(Exception):
    """User-facing error (encrypted, empty, or unreadable PDF)."""


def ensure_pdf2img_folders():
    return ensure_tool_folders(TOOL_SLUG)


def save_upload(file_storage):
    ensure_pdf2img_folders()
    return _save_upload(file_storage, PDF2IMG_INPUT, default_name="document.pdf")


def clamp_dpi(value):
    try:
        n = int(value)
    except (TypeError, ValueError):
        return DEFAULT_DPI
    return max(MIN_DPI, min(MAX_DPI, n))


def render_pdf(input_path, fmt, dpi):
    """Render every page to an image and bundle them into a ZIP.

    Returns (page_count, bundle_path). Raises RenderError on encrypted/empty/bad PDFs.
    """
    ensure_pdf2img_folders()
    ext = _FORMAT_EXT.get(fmt, "png")

    stem = os.path.splitext(os.path.basename(input_path))[0]
    stem = sanitize_filename(stem, default="document")

    try:
        doc = fitz.open(input_path)
    except Exception:
        raise RenderError("Could not open this PDF. It may be corrupt.")

    try:
        if doc.needs_pass:
            raise RenderError("This PDF is password-protected. Unlock it first.")
        if doc.page_count == 0:
            raise RenderError("This PDF has no pages.")

        page_paths = []
        for i in range(doc.page_count):
            page = doc.load_page(i)
            pix = page.get_pixmap(dpi=dpi)  # RGB, no alpha (safe for JPEG)
            out_path = unique_path(PDF2IMG_OUTPUT, f"{stem}_page_{i + 1:03d}.{ext}")
            pix.save(out_path)
            page_paths.append(out_path)
        page_count = doc.page_count
    finally:
        doc.close()

    bundle_path = zip_files_to_path(page_paths, unique_path(PDF2IMG_OUTPUT, f"{stem}_images.zip"))
    return page_count, bundle_path
