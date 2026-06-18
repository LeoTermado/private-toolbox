"""Universal Image Format Changer logic (no Flask).

Converts an uploaded image to another format using Pillow (already installed).
Supports a broad set of common raster formats both as input and output, with
robust colour-mode handling so any supported type can convert to any other.
"""
import os

from PIL import Image

from core.paths import tool_input_dir, tool_output_dir, ensure_tool_folders
from core.uploads import save_upload as _save_upload
from core.filenames import sanitize_filename, unique_path

TOOL_SLUG = "image_format_changer"

IMG_INPUT = tool_input_dir(TOOL_SLUG)
IMG_OUTPUT = tool_output_dir(TOOL_SLUG)

# Input types Pillow reads reliably.
INPUT_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".jfif", ".webp", ".bmp", ".gif",
    ".tiff", ".tif", ".ico", ".tga", ".ppm", ".pgm", ".pbm",
}

# Target formats offered in the UI -> (Pillow format, output extension).
TARGET_FORMATS = [
    ("PNG", "PNG (.png)"),
    ("JPEG", "JPEG (.jpg)"),
    ("WEBP", "WEBP (.webp)"),
    ("BMP", "BMP (.bmp)"),
    ("GIF", "GIF (.gif)"),
    ("TIFF", "TIFF (.tiff)"),
    ("ICO", "ICO (.ico)"),
    ("TGA", "TGA (.tga)"),
    ("PPM", "PPM (.ppm)"),
]
_FORMAT_EXT = {
    "PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp", "BMP": ".bmp",
    "GIF": ".gif", "TIFF": ".tiff", "ICO": ".ico", "TGA": ".tga", "PPM": ".ppm",
}
DEFAULT_FORMAT = "PNG"

# Formats that cannot store an alpha channel.
_NO_ALPHA = {"JPEG", "BMP", "PPM"}


def ensure_image_folders():
    return ensure_tool_folders(TOOL_SLUG)


def save_upload(file_storage):
    ensure_image_folders()
    return _save_upload(file_storage, IMG_INPUT, default_name="image.png")


def is_supported_format(fmt):
    return fmt in _FORMAT_EXT


def _prepare(img, target_format):
    """Coerce the image into a colour mode the target format can store."""
    if target_format in _NO_ALPHA:
        # No alpha: keep grayscale as-is, otherwise flatten to RGB.
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
    else:
        # Alpha-capable (or palette) targets: normalize exotic modes to RGBA,
        # and expand palette images so transparency survives.
        if img.mode == "P":
            img = img.convert("RGBA")
        elif img.mode not in ("RGB", "RGBA", "L", "LA"):
            img = img.convert("RGBA")
    return img


def convert_image(input_path, target_format):
    """Convert the image at input_path to target_format; return the output path."""
    ensure_image_folders()
    stem = os.path.splitext(os.path.basename(input_path))[0]
    stem = sanitize_filename(stem, default="image")
    output_path = unique_path(IMG_OUTPUT, f"{stem}{_FORMAT_EXT[target_format]}")

    with Image.open(input_path) as img:
        prepared = _prepare(img, target_format)
        prepared.save(output_path, format=target_format)

    return output_path
