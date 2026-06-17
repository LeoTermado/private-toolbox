"""PDF Metadata Purge blueprint — remove document metadata from a PDF."""
import os

from flask import Blueprint, render_template, request, flash, redirect, url_for, abort

from core.file_utils import archive_session
from core.downloads import send_pdf_download
from core.validators import is_pdf_filename
from . import service

bp = Blueprint('pdf_metadata_purge', __name__, url_prefix='/pdf/metadata-purge')


@bp.route('/')
def index():
    return render_template('pdf_metadata_purge.html', result=None)


@bp.route('/purge', methods=['POST'])
def purge():
    file = request.files.get('file')
    output_name = request.form.get('output_name', '')

    if file is None or file.filename == '':
        flash("Please select a PDF file.")
        return redirect(url_for('pdf_metadata_purge.index'))

    if not is_pdf_filename(file.filename):
        flash("Only PDF files are allowed.")
        return redirect(url_for('pdf_metadata_purge.index'))

    try:
        input_path = service.save_upload(file)
        out_name = service.build_output_name(output_name, input_path)
        output_path, original = service.purge_metadata(input_path, out_name)
    except ValueError as exc:
        flash(str(exc))
        return redirect(url_for('pdf_metadata_purge.index'))
    except Exception:
        flash("Could not process this PDF. It may be corrupt or unreadable.")
        return redirect(url_for('pdf_metadata_purge.index'))

    view = {
        "download_name": os.path.basename(output_path),
        "original": original,
        "had_metadata": bool(original),
    }
    return render_template('pdf_metadata_purge.html', result=view)


@bp.route('/download/<path:filename>')
def download(filename):
    safe_name = os.path.basename(filename)
    path = os.path.join(service.PURGE_OUTPUT, safe_name)
    if not os.path.isfile(path):
        abort(404)
    return send_pdf_download(path, download_name=safe_name)


@bp.route('/archive', methods=['POST'])
def archive():
    archive_name = archive_session()
    if archive_name is None:
        flash("Nothing to archive! Input and Output folders are already empty.")
    else:
        flash(f"Successfully archived session into old/{archive_name}/ !")
    return redirect(url_for('pdf_metadata_purge.index'))
