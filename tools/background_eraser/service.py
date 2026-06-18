"""Automated Asset Background Eraser logic (no Flask).

Scoped, deterministic background removal: makes a solid / near-uniform
background colour transparent (colour-key) and outputs a PNG with alpha.

This is NOT AI subject detection. It works best on logos, icons, and product
or asset shots on a plain background. Complex photo backgrounds are not removed
reliably — the UI states this honestly.
"""
import os
from collections import Counter

from PIL import Image

from core.paths import tool_input_dir, tool_output_dir, ensure_tool_folders
from core.uploads import save_upload as _save_upload
from core.filenames import sanitize_filename, unique_path

TOOL_SLUG = "background_eraser"

BG_INPUT = tool_input_dir(TOOL_SLUG)
BG_OUTPUT = tool_output_dir(TOOL_SLUG)

INPUT_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff", ".tif"}

BG_CHOICES = [
    ("auto", "Auto-detect from corners"),
    ("white", "White background"),
    ("black", "Black background"),
]
DEFAULT_BG = "auto"
DEFAULT_TOLERANCE = 30


def ensure_bg_folders():
    return ensure_tool_folders(TOOL_SLUG)


def save_upload(file_storage):
    ensure_bg_folders()
    return _save_upload(file_storage, BG_INPUT, default_name="asset.png")


def clamp_tolerance(value):
    try:
        n = int(value)
    except (TypeError, ValueError):
        return DEFAULT_TOLERANCE
    return max(0, min(255, n))


def _target_color(img, bg_choice):
    if bg_choice == "white":
        return (255, 255, 255)
    if bg_choice == "black":
        return (0, 0, 0)
    # auto: most common of the four corner pixels
    w, h = img.size
    corners = [
        img.getpixel((0, 0)),
        img.getpixel((w - 1, 0)),
        img.getpixel((0, h - 1)),
        img.getpixel((w - 1, h - 1)),
    ]
    corners = [c[:3] for c in corners]
    return Counter(corners).most_common(1)[0][0]


def remove_background(input_path, bg_choice, tolerance):
    """Make the background colour transparent; return (output_path, stats).

    stats: {removed, total, percent, color}.
    """
    ensure_bg_folders()
    stem = os.path.splitext(os.path.basename(input_path))[0]
    stem = sanitize_filename(stem, default="asset")
    output_path = unique_path(BG_OUTPUT, f"{stem}_nobg.png")

    with Image.open(input_path) as src:
        img = src.convert("RGBA")
        tr, tg, tb = _target_color(img, bg_choice)

        pixels = list(img.getdata())
        new_pixels = []
        removed = 0
        for r, g, b, a in pixels:
            if abs(r - tr) <= tolerance and abs(g - tg) <= tolerance and abs(b - tb) <= tolerance:
                new_pixels.append((r, g, b, 0))
                removed += 1
            else:
                new_pixels.append((r, g, b, a))
        img.putdata(new_pixels)
        img.save(output_path, "PNG")

    total = len(pixels)
    stats = {
        "removed": removed,
        "total": total,
        "percent": round(removed / total * 100, 1) if total else 0.0,
        "color": f"#{tr:02X}{tg:02X}{tb:02X}",
    }
    return output_path, stats
