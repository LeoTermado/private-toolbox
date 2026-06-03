"""PDF Splitter blueprint — the one fully functional tool."""
from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for

from core.file_utils import archive_session
from . import service

bp = Blueprint('pdf_splitter', __name__, url_prefix='/pdf/splitter')


@bp.route('/')
def index():
    return render_template('pdf_splitter.html')


@bp.route('/split', methods=['POST'])
def split():
    if 'file' not in request.files or not request.form.get('ranges'):
        return redirect(url_for('pdf_splitter.index'))

    file = request.files['file']
    range_string = request.form.get('ranges')

    if file.filename == '' or not file.filename.lower().endswith('.pdf'):
        return "Invalid file format. Please upload a PDF.", 400

    # Save the upload, then split. Files persist in input/ and output/ until archived.
    input_path = service.save_upload(file)
    created_files = service.split_pdf(input_path, range_string)

    if not created_files:
        return "No valid pages were extracted. Check your page range values.", 400

    zip_buffer = service.build_zip(created_files)
    return send_file(
        zip_buffer,
        as_attachment=True,
        download_name="split_pdfs.zip",
        mimetype="application/zip",
    )


@bp.route('/archive', methods=['POST'])
def archive():
    archive_name = archive_session()
    if archive_name is None:
        flash("Nothing to archive! Input and Output folders are already empty.")
    else:
        flash(f"Successfully archived session into old/{archive_name}/ !")
    return redirect(url_for('pdf_splitter.index'))
