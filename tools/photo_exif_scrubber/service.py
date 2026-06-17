"""Photo EXIF Scrubber logic (no Flask).

Removes EXIF / embedded metadata from an image by rebuilding it from raw pixel
data with Pillow (already installed).
"""
import os

from PIL import Image

from core.paths import tool_input_dir, tool_output_dir, ensure_tool_folders
from core.uploads import save_upload as _save_upload
from core.filenames import sanitize_filename, unique_path

TOOL_SLUG = "photo_exif_scrubber"

EXIF_INPUT = tool_input_dir(TOOL_SLUG)
EXIF_OUTPUT = tool_output_dir(TOOL_SLUG)

INPUT_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff", ".tif"}


def ensure_exif_folders():
    return ensure_tool_folders(TOOL_SLUG)


def save_upload(file_storage):
    ensure_exif_folders()
    return _save_upload(file_storage, EXIF_INPUT, default_name="photo.jpg")


def scrub(input_path):
    """Write a metadata-free copy of the image; return (output_path, exif_count).

    exif_count is how many EXIF tags were present in the original (0 if none).
    """
    ensure_exif_folders()
    stem, ext = os.path.splitext(os.path.basename(input_path))
    stem = sanitize_filename(stem, default="photo")
    if not ext:
        ext = ".jpg"
    output_path = unique_path(EXIF_OUTPUT, f"{stem}_clean{ext}")

    with Image.open(input_path) as img:
        try:
            exif_count = len(img.getexif())
        except Exception:
            exif_count = 0

        # Rebuild the image from pixel data so no EXIF/info travels along.
        clean = Image.new(img.mode, img.size)
        clean.putdata(list(img.getdata()))
        if img.mode == "P":
            palette = img.getpalette()
            if palette:
                clean.putpalette(palette)
        clean.save(output_path)

    return output_path, exif_count
