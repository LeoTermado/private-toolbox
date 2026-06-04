"""Flask download-response helpers (route layer).

It is intentional that this module imports Flask — it produces HTTP download
responses. Helpers are generic so future tools can serve PDFs, ZIPs, images,
text, and other outputs.
"""
import os
from io import BytesIO

from flask import send_file

PDF_MIMETYPE = "application/pdf"
ZIP_MIMETYPE = "application/zip"


def file_to_buffer(path):
    """Read a file fully into a BytesIO positioned at the start."""
    buffer = BytesIO()
    with open(path, "rb") as fh:
        buffer.write(fh.read())
    buffer.seek(0)
    return buffer


def send_buffer_download(buffer, download_name, mimetype):
    """Send an in-memory buffer as an attachment download."""
    return send_file(buffer, as_attachment=True, download_name=download_name,
                     mimetype=mimetype)


def send_file_download(path, download_name=None, mimetype=None):
    """Read a file into memory and send it as an attachment.

    Reading into memory means no OS handle is kept on the source file, so it can
    be moved/archived afterwards (notably on Windows). download_name defaults to
    the file's basename.
    """
    if download_name is None:
        download_name = os.path.basename(path)
    return send_buffer_download(file_to_buffer(path), download_name, mimetype)


def send_pdf_download(path, download_name=None):
    """Send a PDF file on disk as an attachment."""
    return send_file_download(path, download_name=download_name, mimetype=PDF_MIMETYPE)


def send_zip_download(buffer, download_name):
    """Send an in-memory ZIP buffer as an attachment."""
    return send_buffer_download(buffer, download_name, ZIP_MIMETYPE)
