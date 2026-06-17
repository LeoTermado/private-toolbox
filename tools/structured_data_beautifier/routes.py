"""Structured Data Beautifier blueprint — pretty-print / minify JSON and XML."""
import os

from flask import Blueprint, render_template, request, flash, redirect, url_for, abort

from core.file_utils import archive_session
from core.downloads import send_file_download
from core.uploads import save_upload
from core.paths import tool_input_dir
from . import service

bp = Blueprint('structured_data_beautifier', __name__, url_prefix='/data/beautifier')

_MIME = {".json": "application/json", ".xml": "application/xml"}


def _render(result=None, fmt=service.DEFAULT_FORMAT, mode=service.DEFAULT_MODE,
            indent=service.DEFAULT_INDENT):
    return render_template('structured_data_beautifier.html', result=result,
                           formats=service.FORMAT_CHOICES, modes=service.MODE_CHOICES,
                           selected_format=fmt, selected_mode=mode, indent=indent)


@bp.route('/')
def index():
    return _render()


@bp.route('/process', methods=['POST'])
def process():
    fmt = request.form.get('format', service.DEFAULT_FORMAT)
    mode = request.form.get('mode', service.DEFAULT_MODE)
    indent = service.clamp_indent(request.form.get('indent', service.DEFAULT_INDENT))
    pasted = request.form.get('data', '')
    file = request.files.get('file')

    # Prefer an uploaded file; fall back to the pasted text.
    text = ""
    if file is not None and file.filename:
        try:
            service.ensure_data_folders()
            path = save_upload(file, tool_input_dir(service.TOOL_SLUG), default_name="data.txt")
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        except Exception:
            flash("Could not read the uploaded file.")
            return redirect(url_for('structured_data_beautifier.index'))
    else:
        text = pasted

    if not text.strip():
        flash("Please paste some JSON/XML or upload a file.")
        return redirect(url_for('structured_data_beautifier.index'))

    try:
        output_text, resolved = service.process(text, fmt, mode, indent)
        out_path = service.save_result(output_text, resolved)
    except service.ParseError as exc:
        flash(str(exc))
        return _render(fmt=fmt, mode=mode, indent=indent)
    except Exception:
        flash("Could not process this data. Please check the format and try again.")
        return _render(fmt=fmt, mode=mode, indent=indent)

    result = {
        "output_text": output_text,
        "resolved_format": resolved.upper(),
        "download_name": os.path.basename(out_path),
    }
    return _render(result=result, fmt=fmt, mode=mode, indent=indent)


@bp.route('/download/<path:filename>')
def download(filename):
    safe_name = os.path.basename(filename)
    path = os.path.join(service.DATA_OUTPUT, safe_name)
    if not os.path.isfile(path):
        abort(404)
    ext = os.path.splitext(safe_name)[1].lower()
    return send_file_download(path, download_name=safe_name,
                             mimetype=_MIME.get(ext, "text/plain"))


@bp.route('/archive', methods=['POST'])
def archive():
    archive_name = archive_session()
    if archive_name is None:
        flash("Nothing to archive! Input and Output folders are already empty.")
    else:
        flash(f"Successfully archived session into old/{archive_name}/ !")
    return redirect(url_for('structured_data_beautifier.index'))
