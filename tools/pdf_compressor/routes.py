"""PDF Compressor blueprint — reduce a PDF's file size."""
import os

from flask import Blueprint, render_template, request, flash, redirect, url_for, abort

from core.file_utils import archive_session
from core.downloads import send_pdf_download
from core.validators import is_pdf_filename
from core.file_size import format_file_size
from . import service

bp = Blueprint('pdf_compressor', __name__, url_prefix='/pdf/compressor')


@bp.route('/')
def index():
    return render_template('pdf_compressor.html', result=None,
                           gs=service.ghostscript_status(),
                           levels=service.LEVEL_CHOICES, selected_level=service.DEFAULT_LEVEL)


@bp.route('/compress', methods=['POST'])
def compress():
    file = request.files.get('file')
    level = request.form.get('level', service.DEFAULT_LEVEL)
    output_name = request.form.get('output_name', '')

    # --- Validation ---
    if file is None or file.filename == '':
        flash("Please select a PDF file to compress.")
        return redirect(url_for('pdf_compressor.index'))

    if not is_pdf_filename(file.filename):
        flash("Only PDF files are allowed.")
        return redirect(url_for('pdf_compressor.index'))

    # --- Compress (guarded so corrupt/unreadable PDFs never crash the server) ---
    try:
        input_path = service.save_upload(file)
        out_name = service.build_output_name(output_name, input_path)
        result = service.compress(input_path, out_name, level)
    except Exception:
        flash("Compression failed: this PDF could not be processed. It may be corrupt or unreadable.")
        return redirect(url_for('pdf_compressor.index'))

    if not result.ok:
        detail = result.error or "Unknown error."
        flash(f"Compression failed: {detail}")
        return redirect(url_for('pdf_compressor.index'))

    view = {
        "download_name": os.path.basename(result.output_path),
        "original_human": format_file_size(result.original_bytes),
        "output_human": format_file_size(result.output_bytes),
        "saved_human": format_file_size(result.saved_bytes),
        "saved_percent": result.saved_percent,
        "smaller": result.smaller,
        "basic_used": result.engine == "basic",
    }
    return render_template('pdf_compressor.html', result=view,
                           gs=service.ghostscript_status(),
                           levels=service.LEVEL_CHOICES, selected_level=level)


@bp.route('/ghostscript-help')
def ghostscript_help():
    return render_template('ghostscript_help.html')


@bp.route('/download/<path:filename>')
def download(filename):
    # Only serve files that actually live in the compressor output folder.
    safe_name = os.path.basename(filename)
    path = os.path.join(service.COMPRESSOR_OUTPUT, safe_name)
    if not os.path.isfile(path):
        abort(404)
    return send_pdf_download(path, download_name=safe_name)


@bp.route('/archive', methods=['POST'])
def archive():
    # Same global archive behavior as the other tools: moves the whole input/
    # and output/ workspace into old/archive_<timestamp>/.
    archive_name = archive_session()
    if archive_name is None:
        flash("Nothing to archive! Input and Output folders are already empty.")
    else:
        flash(f"Successfully archived session into old/{archive_name}/ !")
    return redirect(url_for('pdf_compressor.index'))
