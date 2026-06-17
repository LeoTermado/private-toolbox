"""PDF Password Guard blueprint — add or remove a PDF password."""
import os

from flask import Blueprint, render_template, request, flash, redirect, url_for, abort

from core.file_utils import archive_session
from core.downloads import send_pdf_download
from core.validators import is_pdf_filename
from . import service

bp = Blueprint('pdf_password_guard', __name__, url_prefix='/pdf/password-guard')


@bp.route('/')
def index():
    return render_template('pdf_password_guard.html', result=None,
                           modes=service.MODE_CHOICES, selected_mode=service.DEFAULT_MODE)


@bp.route('/process', methods=['POST'])
def process():
    file = request.files.get('file')
    mode = request.form.get('mode', service.DEFAULT_MODE)
    password = request.form.get('password', '')

    if file is None or file.filename == '':
        flash("Please select a PDF file.")
        return redirect(url_for('pdf_password_guard.index'))

    if not is_pdf_filename(file.filename):
        flash("Only PDF files are allowed.")
        return redirect(url_for('pdf_password_guard.index'))

    if mode not in {m[0] for m in service.MODE_CHOICES}:
        mode = service.DEFAULT_MODE

    if not password:
        flash("Please enter a password.")
        return redirect(url_for('pdf_password_guard.index'))

    try:
        input_path = service.save_upload(file)
        if mode == "protect":
            output_path = service.protect(input_path, password)
            action = "protected"
        else:
            output_path = service.unlock(input_path, password)
            action = "unlocked"
    except service.GuardError as exc:
        flash(str(exc))
        return redirect(url_for('pdf_password_guard.index'))
    except Exception:
        flash("Could not process this PDF. Please try again.")
        return redirect(url_for('pdf_password_guard.index'))

    view = {"download_name": os.path.basename(output_path), "action": action}
    return render_template('pdf_password_guard.html', result=view,
                           modes=service.MODE_CHOICES, selected_mode=mode)


@bp.route('/download/<path:filename>')
def download(filename):
    safe_name = os.path.basename(filename)
    path = os.path.join(service.GUARD_OUTPUT, safe_name)
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
    return redirect(url_for('pdf_password_guard.index'))
