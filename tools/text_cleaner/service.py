"""Text Cleaner logic (no Flask).

Normalizes and tidies plain text using only the standard library.
"""
import os
import re

from core.paths import tool_input_dir, tool_output_dir, ensure_tool_folders
from core.filenames import unique_path

TOOL_SLUG = "text_cleaner"

TEXT_INPUT = tool_input_dir(TOOL_SLUG)
TEXT_OUTPUT = tool_output_dir(TOOL_SLUG)

# (form value, label, default-checked)
OPTION_CHOICES = [
    ("trim_lines", "Trim spaces at the start/end of each line", True),
    ("collapse_spaces", "Collapse repeated spaces/tabs into one", False),
    ("remove_blank_lines", "Remove all blank lines", False),
    ("collapse_blank_lines", "Collapse multiple blank lines into one", True),
    ("trim_document", "Trim blank lines at the very start/end", True),
]
DEFAULT_OPTIONS = [key for key, _label, default in OPTION_CHOICES if default]


def ensure_text_folders():
    return ensure_tool_folders(TOOL_SLUG)


def clean_text(text, options):
    """Apply the selected cleaning options and return the cleaned text.

    Line endings are always normalized to '\\n'.
    """
    opts = set(options or [])
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")

    if "trim_lines" in opts:
        lines = [ln.strip() for ln in lines]
    if "collapse_spaces" in opts:
        lines = [re.sub(r"[ \t]+", " ", ln) for ln in lines]
    if "remove_blank_lines" in opts:
        lines = [ln for ln in lines if ln.strip() != ""]

    text = "\n".join(lines)

    if "collapse_blank_lines" in opts:
        text = re.sub(r"\n{3,}", "\n\n", text)
    if "trim_document" in opts:
        text = text.strip("\n")

    return text


def stats(text):
    """Return {chars, lines} for a block of text."""
    return {"chars": len(text), "lines": len(text.split("\n")) if text else 0}


def save_result(text):
    """Write the cleaned text to output/ and return its path."""
    ensure_text_folders()
    out_path = unique_path(TEXT_OUTPUT, "cleaned.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    return out_path
