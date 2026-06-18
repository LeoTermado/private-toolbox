"""Launcher for the Private Toolbox web app.

Run this to start the server locally:

    python run.py

Then open http://127.0.0.1:5000 in your browser.

(The old command-line PDF splitter that used to live here has moved to
cli_splitter.py.)
"""
import os

from app import create_app
from core.paths import INPUT_FOLDER, OUTPUT_FOLDER, OLD_FOLDER

# Keep the debug auto-reloader from restarting the server when tools write into
# the working folders. Otherwise generating output mid-request can restart the
# server and drop the response/download (most visible on large/slow jobs).
#
# reloader_type='stat' only watches imported Python modules, so it never sees
# files written into input/ output/ old/ — but still reloads on code edits.
# The exclude_patterns are belt-and-suspenders for the stat reloader.
RELOADER_EXCLUDE = [
    os.path.join(INPUT_FOLDER, '*'),
    os.path.join(OUTPUT_FOLDER, '*'),
    os.path.join(OLD_FOLDER, '*'),
]

if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5000, debug=True,
            reloader_type='stat', exclude_patterns=RELOADER_EXCLUDE)
