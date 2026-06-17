"""Image Resizer & Compressor blueprint — shrink/recompress an image."""
import mimetypes
import os

from flask import Blueprint, render_template, request, flash, redirect, url_for, abort

from core.file_utils import archive_session
from core.downloads import send_file_download
from core.validators import has_allowed_extension
from core.file_size import compare_files
from . import service

bp = Blueprint('image_resizer_compressor', __name__, url_prefix='/image/resizer-compressor')


@bp.route('/')
def index():
    return render_template('image_resizer_compressor.html', result=None,
                           default_quality=service.DEFAULT_QUALITY)


@bp.route('/process', methods=['POST'])
def process():
    file = request.files.get('file')
    max_width = request.form.get('max_width', '')
    max_height = request.form.get('max_height', '')
    quality = service.clamp_quality(request.form.get('quality', service.DEFAULT_QUALITY))

    if file is None or file.filename == '':
        flash("Please select an image.")
        return redirect(url_for('image_resizer_compressor.index'))

    if not has_allowed_extension(file.filename, service.INPUT_EXTENSIONS):
        flash("Unsupported image type. Use PNG, JPG, WEBP, BMP, GIF or TIFF.")
        return redirect(url_for('image_resizer_compressor.index'))

    try:
        input_path = service.save_upload(file)
        output_path, info = service.process_image(input_path, max_width, max_height, quality)
    except Exception:
        flash("Could not process this image. It may be corrupt or unsupported.")
        return redirect(url_for('image_resizer_compressor.index'))

    sizes = compare_files(input_path, output_path)
    view = {
        "download_name": os.path.basename(output_path),
        "original_human": sizes["original_human"],
        "output_human": sizes["output_human"],
        "saved_human": sizes["saved_human"],
        "saved_percent": sizes["saved_percent"],
        "smaller": sizes["smaller"],
        "original_dims": f"{info['original_width']}×{info['original_height']}",
        "new_dims": f"{info['new_width']}×{info['new_height']}",
        "quality": quality,
    }
    return render_template('image_resizer_compressor.html', result=view,
                           default_quality=quality)


@bp.route('/download/<path:filename>')
def download(filename):
    safe_name = os.path.basename(filename)
    path = os.path.join(service.RC_OUTPUT, safe_name)
    if not os.path.isfile(path):
        abort(404)
    mimetype = mimetypes.guess_type(safe_name)[0] or "application/octet-stream"
    return send_file_download(path, download_name=safe_name, mimetype=mimetype)


@bp.route('/archive', methods=['POST'])
def archive():
    archive_name = archive_session()
    if archive_name is None:
        flash("Nothing to archive! Input and Output folders are already empty.")
    else:
        flash(f"Successfully archived session into old/{archive_name}/ !")
    return redirect(url_for('image_resizer_compressor.index'))
