"""Image to PDF logic (no Flask).

Combines one or more uploaded images into a single PDF using Pillow
(already installed).
"""
import os

from PIL import Image

from core.paths import tool_input_dir, tool_output_dir, ensure_tool_folders
from core.uploads import save_uploads as _save_uploads
from core.filenames import sanitize_output_filename, unique_path

TOOL_SLUG = "image_to_pdf"

IMG_INPUT = tool_input_dir(TOOL_SLUG)
IMG_OUTPUT = tool_output_dir(TOOL_SLUG)

INPUT_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff", ".tif"}


def ensure_image_folders():
    return ensure_tool_folders(TOOL_SLUG)


def save_uploads(file_storages):
    ensure_image_folders()
    return _save_uploads(file_storages, IMG_INPUT, default_name="image.png")


def build_output_name(raw_name):
    """Return a safe '<name>.pdf' (defaults to images.pdf)."""
    return sanitize_output_filename(raw_name, ".pdf") or "images.pdf"


def images_to_pdf(input_paths, output_name):
    """Combine the images at input_paths (in order) into one PDF; return its path."""
    ensure_image_folders()
    output_path = unique_path(IMG_OUTPUT, output_name)

    pages = []
    for path in input_paths:
        with Image.open(path) as img:
            # PDF pages must be RGB (no alpha); convert a copy so the file handle
            # can close immediately.
            pages.append(img.convert("RGB"))

    pages[0].save(output_path, "PDF", save_all=True, append_images=pages[1:])
    return output_path
