"""Text Cleaner blueprint — normalize and tidy plain text."""
import os

from flask import Blueprint, render_template, request, flash, redirect, url_for, abort

from core.file_utils import archive_session
from core.downloads import send_file_download
from core.uploads import save_upload
from core.paths import tool_input_dir
from . import service

bp = Blueprint('text_cleaner', __name__, url_prefix='/text/cleaner')


def _render(result=None, selected_options=None):
    return render_template('text_cleaner.html', result=result,
                           options=service.OPTION_CHOICES,
                           selected_options=selected_options or service.DEFAULT_OPTIONS)


@bp.route('/')
def index():
    return _render()


@bp.route('/clean', methods=['POST'])
def clean():
    pasted = request.form.get('text', '')
    options = request.form.getlist('options')
    file = request.files.get('file')

    text = ""
    if file is not None and file.filename:
        try:
            service.ensure_text_folders()
            path = save_upload(file, tool_input_dir(service.TOOL_SLUG), default_name="text.txt")
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        except Exception:
            flash("Could not read the uploaded file.")
            return redirect(url_for('text_cleaner.index'))
    else:
        text = pasted

    if not text.strip():
        flash("Please paste some text or upload a text file.")
        return redirect(url_for('text_cleaner.index'))

    try:
        cleaned = service.clean_text(text, options)
        out_path = service.save_result(cleaned)
    except Exception:
        flash("Could not clean this text. Please try again.")
        return _render(selected_options=options)

    result = {
        "output_text": cleaned,
        "download_name": os.path.basename(out_path),
        "before": service.stats(text),
        "after": service.stats(cleaned),
    }
    return _render(result=result, selected_options=options)


@bp.route('/download/<path:filename>')
def download(filename):
    safe_name = os.path.basename(filename)
    path = os.path.join(service.TEXT_OUTPUT, safe_name)
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
    return redirect(url_for('text_cleaner.index'))
