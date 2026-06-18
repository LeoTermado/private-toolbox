"""PDF to Image blueprint — render PDF pages to images (ZIP download)."""
import os

from flask import Blueprint, render_template, request, flash, redirect, url_for, abort

from core.file_utils import archive_session
from core.downloads import send_file_download
from core.validators import is_pdf_filename
from . import service

bp = Blueprint('pdf_to_image', __name__, url_prefix='/pdf/to-image')


@bp.route('/')
def index():
    return render_template('pdf_to_image.html', result=None,
                           formats=service.FORMAT_CHOICES, selected_format=service.DEFAULT_FORMAT,
                           dpi=service.DEFAULT_DPI)


@bp.route('/convert', methods=['POST'])
def convert():
    file = request.files.get('file')
    fmt = request.form.get('format', service.DEFAULT_FORMAT)
    dpi = service.clamp_dpi(request.form.get('dpi', service.DEFAULT_DPI))

    if file is None or file.filename == '':
        flash("Please select a PDF file.")
        return redirect(url_for('pdf_to_image.index'))

    if not is_pdf_filename(file.filename):
        flash("Only PDF files are allowed.")
        return redirect(url_for('pdf_to_image.index'))

    if fmt not in {f[0] for f in service.FORMAT_CHOICES}:
        fmt = service.DEFAULT_FORMAT

    try:
        input_path = service.save_upload(file)
        page_count, bundle_path = service.render_pdf(input_path, fmt, dpi)
    except service.RenderError as exc:
        flash(str(exc))
        return redirect(url_for('pdf_to_image.index'))
    except Exception:
        flash("Could not convert this PDF. It may be corrupt or unsupported.")
        return redirect(url_for('pdf_to_image.index'))

    view = {
        "page_count": page_count,
        "format": fmt.upper(),
        "dpi": dpi,
        "bundle_name": os.path.basename(bundle_path),
    }
    return render_template('pdf_to_image.html', result=view,
                           formats=service.FORMAT_CHOICES, selected_format=fmt, dpi=dpi)


@bp.route('/download/<path:filename>')
def download(filename):
    safe_name = os.path.basename(filename)
    path = os.path.join(service.PDF2IMG_OUTPUT, safe_name)
    if not os.path.isfile(path):
        abort(404)
    return send_file_download(path, download_name=safe_name, mimetype="application/zip")


@bp.route('/archive', methods=['POST'])
def archive():
    archive_name = archive_session()
    if archive_name is None:
        flash("Nothing to archive! Input and Output folders are already empty.")
    else:
        flash(f"Successfully archived session into old/{archive_name}/ !")
    return redirect(url_for('pdf_to_image.index'))
