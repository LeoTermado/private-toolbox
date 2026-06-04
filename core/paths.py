"""Project path constants and folder helpers.

Single source of truth for where files live. Tools should derive their
per-tool subfolders from here (input/<tool>/ and output/<tool>/).
"""
import os

# Project root = parent of the core/ package.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FOLDER = os.path.join(BASE_DIR, 'input')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'output')
OLD_FOLDER = os.path.join(BASE_DIR, 'old')


def ensure_base_folders():
    """Create input/, output/ and old/ if they don't exist."""
    os.makedirs(INPUT_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    os.makedirs(OLD_FOLDER, exist_ok=True)


def tool_input_dir(tool_slug):
    """Return input/<tool_slug> (not created here)."""
    return os.path.join(INPUT_FOLDER, tool_slug)


def tool_output_dir(tool_slug):
    """Return output/<tool_slug> (not created here)."""
    return os.path.join(OUTPUT_FOLDER, tool_slug)


def ensure_tool_folders(tool_slug):
    """Create input/<tool_slug> and output/<tool_slug>; return (input_dir, output_dir)."""
    in_dir = tool_input_dir(tool_slug)
    out_dir = tool_output_dir(tool_slug)
    os.makedirs(in_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)
    return in_dir, out_dir
