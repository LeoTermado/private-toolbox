"""Structured Data Beautifier logic (no Flask).

Pretty-prints or minifies JSON and XML using only the standard library
(json + xml.dom.minidom).
"""
import json
import os
import re
from xml.dom import minidom
from xml.parsers.expat import ExpatError

from core.paths import tool_input_dir, tool_output_dir, ensure_tool_folders
from core.filenames import unique_path

TOOL_SLUG = "structured_data_beautifier"

DATA_INPUT = tool_input_dir(TOOL_SLUG)
DATA_OUTPUT = tool_output_dir(TOOL_SLUG)

FORMAT_CHOICES = [("auto", "Auto-detect"), ("json", "JSON"), ("xml", "XML")]
MODE_CHOICES = [("beautify", "Beautify (pretty-print)"), ("minify", "Minify")]
DEFAULT_FORMAT = "auto"
DEFAULT_MODE = "beautify"
DEFAULT_INDENT = 2

_EXT = {"json": ".json", "xml": ".xml"}


class ParseError(Exception):
    """Raised when the input can't be parsed as the detected/selected format."""


def ensure_data_folders():
    return ensure_tool_folders(TOOL_SLUG)


def clamp_indent(value):
    try:
        n = int(value)
    except (TypeError, ValueError):
        return DEFAULT_INDENT
    return max(0, min(8, n))


def detect_format(text, fmt):
    if fmt in ("json", "xml"):
        return fmt
    stripped = text.lstrip()
    if stripped[:1] in "{[":
        return "json"
    if stripped[:1] == "<":
        return "xml"
    # Last resort: try JSON, else assume XML.
    try:
        json.loads(text)
        return "json"
    except ValueError:
        return "xml"


def process(text, fmt, mode, indent):
    """Return (output_text, resolved_format). Raises ParseError on bad input."""
    resolved = detect_format(text, fmt)
    if resolved == "json":
        try:
            obj = json.loads(text)
        except ValueError as exc:
            raise ParseError(f"Invalid JSON: {exc}")
        if mode == "minify":
            return json.dumps(obj, separators=(",", ":"), ensure_ascii=False), "json"
        return json.dumps(obj, indent=indent, ensure_ascii=False), "json"

    # XML
    try:
        dom = minidom.parseString(text.strip())
    except (ExpatError, ValueError) as exc:
        raise ParseError(f"Invalid XML: {exc}")
    if mode == "minify":
        compact = re.sub(r">\s+<", "><", dom.toxml())
        return compact.strip(), "xml"
    pretty = dom.toprettyxml(indent=" " * indent)
    # minidom adds blank lines; drop them.
    lines = [ln for ln in pretty.split("\n") if ln.strip()]
    return "\n".join(lines), "xml"


def save_result(text, resolved_format):
    """Write the formatted text to output/ and return its path."""
    ensure_data_folders()
    ext = _EXT.get(resolved_format, ".txt")
    out_path = unique_path(DATA_OUTPUT, f"beautified{ext}")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    return out_path
