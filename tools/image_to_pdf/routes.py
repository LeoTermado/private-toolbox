"""Image to PDF blueprint — combine images into a single PDF."""
import os

from flask import Blueprint, render_template, request, flash, redirect, url_for, abort

from core.file_utils import archive_session
from core.downloads import send_pdf_download
from core.validators import has_allowed_extension, filter_nonempty_uploads, validate_upload_count
from core.file_size import get_file_size, format_file_size
from . import service

bp = Blueprint('image_to_pdf', __name__, url_prefix='/image/to-pdf')


@bp.route('/')
def index():
    return render_template('image_to_pdf.html', result=None)


@bp.route('/convert', methods=['POST'])
def convert():
    files = filter_nonempty_uploads(request.files.getlist('files'))
    output_name = request.form.get('output_name', '')

    if not validate_upload_count(files, min_count=1):
        flash("Please select at least one image.")
        return redirect(url_for('image_to_pdf.index'))

    if any(not has_allowed_extension(f.filename, service.INPUT_EXTENSIONS) for f in files):
        flash("Unsupported image type. Use PNG, JPG, WEBP, BMP, GIF or TIFF.")
        return redirect(url_for('image_to_pdf.index'))

    try:
        input_paths = service.save_uploads(files)
        out_name = service.build_output_name(output_name)
        output_path = service.images_to_pdf(input_paths, out_name)
    except Exception:
        flash("Could not build a PDF from these images. One may be corrupt or unsupported.")
        return redirect(url_for('image_to_pdf.index'))

    view = {
        "download_name": os.path.basename(output_path),
        "image_count": len(input_paths),
        "output_human": format_file_size(get_file_size(output_path)),
    }
    return render_template('image_to_pdf.html', result=view)


@bp.route('/download/<path:filename>')
def download(filename):
    safe_name = os.path.basename(filename)
    path = os.path.join(service.IMG_OUTPUT, safe_name)
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
    return redirect(url_for('image_to_pdf.index'))
