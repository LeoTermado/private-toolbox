"""Global archive logic.

Moves the current input/ and output/ workspace into a timestamped folder under
old/. Behavior is unchanged from the original core.file_utils.archive_session().
"""
import os
import shutil
from datetime import datetime

from core.paths import INPUT_FOLDER, OUTPUT_FOLDER, OLD_FOLDER


def archive_session(input_folder=INPUT_FOLDER, output_folder=OUTPUT_FOLDER, old_folder=OLD_FOLDER):
    """Move everything in input/ and output/ into a timestamped folder under old/.

    Returns the archive folder name (e.g. 'archive_20260603_134522') on success,
    or None if there was nothing to archive.
    """
    input_contents = os.listdir(input_folder) if os.path.isdir(input_folder) else []
    output_contents = os.listdir(output_folder) if os.path.isdir(output_folder) else []

    if not input_contents and not output_contents:
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"archive_{timestamp}"
    session_archive_dir = os.path.join(old_folder, archive_name)

    archive_input_dir = os.path.join(session_archive_dir, 'input')
    archive_output_dir = os.path.join(session_archive_dir, 'output')
    os.makedirs(archive_input_dir, exist_ok=True)
    os.makedirs(archive_output_dir, exist_ok=True)

    for filename in input_contents:
        shutil.move(os.path.join(input_folder, filename),
                    os.path.join(archive_input_dir, filename))

    for filename in output_contents:
        shutil.move(os.path.join(output_folder, filename),
                    os.path.join(archive_output_dir, filename))

    return archive_name
