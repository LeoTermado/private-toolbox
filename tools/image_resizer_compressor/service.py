"""Image Resizer & Compressor logic (no Flask).

Resizes (keeping aspect ratio) and/or recompresses an uploaded image using
Pillow (already installed).
"""
import os

from PIL import Image

from core.paths import tool_input_dir, tool_output_dir, ensure_tool_folders
from core.uploads import save_upload as _save_upload
from core.filenames import sanitize_filename, unique_path

TOOL_SLUG = "image_resizer_compressor"

RC_INPUT = tool_input_dir(TOOL_SLUG)
RC_OUTPUT = tool_output_dir(TOOL_SLUG)

INPUT_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff", ".tif"}
DEFAULT_QUALITY = 80


def ensure_rc_folders():
    return ensure_tool_folders(TOOL_SLUG)


def save_upload(file_storage):
    ensure_rc_folders()
    return _save_upload(file_storage, RC_INPUT, default_name="image.jpg")


def clamp_quality(value):
    """Coerce a quality value into the 1–100 range (defaults on bad input)."""
    try:
        q = int(value)
    except (TypeError, ValueError):
        return DEFAULT_QUALITY
    return max(1, min(100, q))


def _parse_dim(value):
    """Return a positive int dimension, or None if blank/invalid."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def process_image(input_path, max_width, max_height, quality):
    """Resize/compress the image; return (output_path, info dict).

    info: original_width/height, new_width/height.
    """
    ensure_rc_folders()
    stem, ext = os.path.splitext(os.path.basename(input_path))
    stem = sanitize_filename(stem, default="image")
    if not ext:
        ext = ".jpg"
    output_path = unique_path(RC_OUTPUT, f"{stem}_optimized{ext}")

    max_w = _parse_dim(max_width)
    max_h = _parse_dim(max_height)

    with Image.open(input_path) as img:
        fmt = img.format
        orig_w, orig_h = img.size

        if max_w or max_h:
            img.thumbnail((max_w or img.width, max_h or img.height))

        save_kwargs = {}
        if fmt in ("JPEG", "WEBP"):
            save_kwargs["quality"] = quality
            save_kwargs["optimize"] = True
        elif fmt == "PNG":
            save_kwargs["optimize"] = True

        if fmt == "JPEG" and img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")

        img.save(output_path, **save_kwargs)
        new_w, new_h = img.size

    info = {
        "original_width": orig_w, "original_height": orig_h,
        "new_width": new_w, "new_height": new_h,
    }
    return output_path, info
