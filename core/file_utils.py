"""Central project paths and shared file helpers.

Keeps the input/output/old folder locations and the archive logic in one place
so tools don't each re-derive them. Paths are unchanged from the original app.py.
"""
import os
import shutil
from datetime import datetime

# Project root = parent of the core/ package.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FOLDER = os.path.join(BASE_DIR, 'input')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'output')
OLD_FOLDER = os.path.join(BASE_DIR, 'old')


def ensure_folders():
    """Make sure the core working directories exist."""
    os.makedirs(INPUT_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    os.makedirs(OLD_FOLDER, exist_ok=True)


def archive_session():
    """Move everything in input/ and output/ into a timestamped folder under old/.

    Returns the archive folder name (e.g. 'archive_20260603_134522') on success,
    or None if there was nothing to archive.
    """
    input_contents = os.listdir(INPUT_FOLDER) if os.path.isdir(INPUT_FOLDER) else []
    output_contents = os.listdir(OUTPUT_FOLDER) if os.path.isdir(OUTPUT_FOLDER) else []

    if not input_contents and not output_contents:
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"archive_{timestamp}"
    session_archive_dir = os.path.join(OLD_FOLDER, archive_name)

    archive_input_dir = os.path.join(session_archive_dir, 'input')
    archive_output_dir = os.path.join(session_archive_dir, 'output')
    os.makedirs(archive_input_dir, exist_ok=True)
    os.makedirs(archive_output_dir, exist_ok=True)

    for filename in input_contents:
        shutil.move(os.path.join(INPUT_FOLDER, filename),
                    os.path.join(archive_input_dir, filename))

    for filename in output_contents:
        shutil.move(os.path.join(OUTPUT_FOLDER, filename),
                    os.path.join(archive_output_dir, filename))

    return archive_name
