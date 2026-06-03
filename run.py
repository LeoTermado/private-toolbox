"""Launcher for the Private Toolbox web app.

Run this to start the server locally:

    python run.py

Then open http://127.0.0.1:5000 in your browser.

(The old command-line PDF splitter that used to live here has moved to
cli_splitter.py.)
"""
from app import create_app

if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5000, debug=True)
