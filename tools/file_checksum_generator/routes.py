"""File Checksum Generator blueprint — compute hashes for uploaded files."""
import os

from flask import Blueprint, render_template, request, flash, redirect, url_for, abort

from core.file_utils import archive_session
from core.downloads import send_file_download
from core.validators import filter_nonempty_uploads, validate_upload_count
from core.file_size import get_file_size, format_file_size
from . import service

bp = Blueprint('file_checksum_generator', __name__, url_prefix='/files/checksum')


@bp.route('/')
def index():
    return render_template('file_checksum_generator.html', result=None,
                           algorithms=service.ALGORITHMS,
                           selected_algos=service.DEFAULT_ALGORITHMS)


@bp.route('/generate', methods=['POST'])
def generate():
    files = filter_nonempty_uploads(request.files.getlist('files'))
    algos = service.normalize_algorithms(request.form.getlist('algos'))

    if not validate_upload_count(files, min_count=1):
        flash("Please select at least one file.")
        return redirect(url_for('file_checksum_generator.index'))

    try:
        paths = service.save_uploads(files)
        rows = []
        for path in paths:
            rows.append({
                "name": os.path.basename(path),
                "size_human": format_file_size(get_file_size(path)),
                "hashes": service.compute_checksums(path, algos),
            })
        report_path = service.write_report(rows, algos)
    except Exception:
        flash("Could not generate checksums for these files. Please try again.")
        return redirect(url_for('file_checksum_generator.index'))

    view = {
        "algos": algos,
        "rows": rows,
        "report_name": os.path.basename(report_path),
    }
    return render_template('file_checksum_generator.html', result=view,
                           algorithms=service.ALGORITHMS, selected_algos=algos)


@bp.route('/download/<path:filename>')
def download(filename):
    safe_name = os.path.basename(filename)
    path = os.path.join(service.CHECKSUM_OUTPUT, safe_name)
    if not os.path.isfile(path):
        abort(404)
    return send_file_download(path, download_name=safe_name, mimetype="text/plain")


@bp.route('/archive', methods=['POST'])
def archive():
    archive_name = archive_session()
    if archive_name is None:
        flash("Nothing to archive! Input and Output folders are already empty.")
    else:
        flash(f"Successfully archived session into old/{archive_name}/ !")
    return redirect(url_for('file_checksum_generator.index'))
