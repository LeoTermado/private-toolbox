"""PDF Merger blueprint — combine multiple PDFs into one."""
import os
from io import BytesIO

from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for

from core.file_utils import archive_session
from . import service

bp = Blueprint('pdf_merger', __name__, url_prefix='/pdf/merger')


@bp.route('/')
def index():
    return render_template('pdf_merger.html')


@bp.route('/merge', methods=['POST'])
def merge():
    files = request.files.getlist('files')
    # Drop empty file fields (a browser may send one with no filename).
    files = [f for f in files if f and f.filename]
    output_name = request.form.get('output_name', '')

    # --- Validation ---
    if len(files) < 2:
        flash("Please select at least 2 PDF files to merge.")
        return redirect(url_for('pdf_merger.index'))

    if any(not f.filename.lower().endswith('.pdf') for f in files):
        flash("Only PDF files are allowed.")
        return redirect(url_for('pdf_merger.index'))

    safe_output = service.sanitize_output_name(output_name)
    if safe_output is None:
        flash("Please enter a valid output file name.")
        return redirect(url_for('pdf_merger.index'))

    # --- Merge ---
    input_paths = service.save_uploads(files)  # also ensures the merger folders exist
    output_path = service.unique_path(service.MERGER_OUTPUT, safe_output)
    service.merge_pdfs(input_paths, output_path)

    # Send an in-memory copy so we don't keep a handle on the saved file
    # (this lets the Archive button move output/ afterwards on Windows). The
    # merged PDF still persists on disk in output/pdf_merger/ for archiving.
    buffer = BytesIO()
    with open(output_path, "rb") as fh:
        buffer.write(fh.read())
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=os.path.basename(output_path),
        mimetype="application/pdf",
    )


@bp.route('/archive', methods=['POST'])
def archive():
    # Same global archive behavior as the PDF Splitter: moves the whole
    # input/ and output/ workspace into old/archive_<timestamp>/.
    archive_name = archive_session()
    if archive_name is None:
        flash("Nothing to archive! Input and Output folders are already empty.")
    else:
        flash(f"Successfully archived session into old/{archive_name}/ !")
    return redirect(url_for('pdf_merger.index'))
