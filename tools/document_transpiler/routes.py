"""Advanced Document Transpiler blueprint — Markdown to HTML (scoped)."""
import os

from flask import Blueprint, render_template, request, flash, redirect, url_for, abort

from core.file_utils import archive_session
from core.downloads import send_file_download
from core.uploads import save_upload
from core.validators import has_allowed_extension
from core.paths import tool_input_dir
from . import service

bp = Blueprint('document_transpiler', __name__, url_prefix='/documents/transpiler')


def _render(result=None, conversion=service.DEFAULT_CONVERSION, output_name=""):
    return render_template('document_transpiler.html', result=result,
                           conversions=service.CONVERSIONS,
                           selected_conversion=conversion, output_name=output_name)


@bp.route('/')
def index():
    return _render()


@bp.route('/convert', methods=['POST'])
def convert():
    conversion = request.form.get('conversion', service.DEFAULT_CONVERSION)
    output_name = request.form.get('output_name', '').strip()
    pasted = request.form.get('content', '')
    file = request.files.get('file')

    if conversion not in {c[0] for c in service.CONVERSIONS}:
        conversion = service.DEFAULT_CONVERSION

    # Prefer an uploaded file; fall back to pasted text.
    text = ""
    base = output_name or "document"
    if file is not None and file.filename:
        if not has_allowed_extension(file.filename, service.INPUT_EXTENSIONS):
            flash("Unsupported file type. Upload a .md, .markdown or .txt file.")
            return redirect(url_for('document_transpiler.index'))
        try:
            service.ensure_doc_folders()
            path = save_upload(file, tool_input_dir(service.TOOL_SLUG), default_name="document.md")
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
            if not output_name:
                base = os.path.splitext(os.path.basename(path))[0]
        except Exception:
            flash("Could not read the uploaded file.")
            return redirect(url_for('document_transpiler.index'))
    else:
        text = pasted

    if not text.strip():
        flash("Please paste some Markdown or upload a file.")
        return redirect(url_for('document_transpiler.index'))

    try:
        out_path, html = service.convert(text, base)
    except Exception:
        flash("Could not convert this document. Please try again.")
        return _render(conversion=conversion, output_name=output_name)

    result = {
        "output_text": html,
        "download_name": os.path.basename(out_path),
    }
    return _render(result=result, conversion=conversion, output_name=output_name)


@bp.route('/download/<path:filename>')
def download(filename):
    safe_name = os.path.basename(filename)
    path = os.path.join(service.DOC_OUTPUT, safe_name)
    if not os.path.isfile(path):
        abort(404)
    return send_file_download(path, download_name=safe_name, mimetype="text/html")


@bp.route('/archive', methods=['POST'])
def archive():
    archive_name = archive_session()
    if archive_name is None:
        flash("Nothing to archive! Input and Output folders are already empty.")
    else:
        flash(f"Successfully archived session into old/{archive_name}/ !")
    return redirect(url_for('document_transpiler.index'))
