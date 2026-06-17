"""Universal Image Format Changer blueprint — convert an image to another format."""
import mimetypes
import os

from flask import Blueprint, render_template, request, flash, redirect, url_for, abort

from core.file_utils import archive_session
from core.downloads import send_file_download
from core.validators import has_allowed_extension
from core.file_size import compare_files
from . import service

bp = Blueprint('image_format_changer', __name__, url_prefix='/image/format-changer')


@bp.route('/')
def index():
    return render_template('image_format_changer.html', result=None,
                           formats=service.TARGET_FORMATS, selected_format=service.DEFAULT_FORMAT)


@bp.route('/convert', methods=['POST'])
def convert():
    file = request.files.get('file')
    target = request.form.get('target_format', service.DEFAULT_FORMAT)

    if file is None or file.filename == '':
        flash("Please select an image to convert.")
        return redirect(url_for('image_format_changer.index'))

    if not has_allowed_extension(file.filename, service.INPUT_EXTENSIONS):
        flash("Unsupported image type. Use PNG, JPG, WEBP, BMP, GIF or TIFF.")
        return redirect(url_for('image_format_changer.index'))

    if not service.is_supported_format(target):
        flash("Please choose a valid target format.")
        return redirect(url_for('image_format_changer.index'))

    try:
        input_path = service.save_upload(file)
        output_path = service.convert_image(input_path, target)
    except Exception:
        flash("Could not convert this image. It may be corrupt or unsupported.")
        return redirect(url_for('image_format_changer.index'))

    sizes = compare_files(input_path, output_path)
    view = {
        "download_name": os.path.basename(output_path),
        "target": target,
        "original_human": sizes["original_human"],
        "output_human": sizes["output_human"],
    }
    return render_template('image_format_changer.html', result=view,
                           formats=service.TARGET_FORMATS, selected_format=target)


@bp.route('/download/<path:filename>')
def download(filename):
    safe_name = os.path.basename(filename)
    path = os.path.join(service.IMG_OUTPUT, safe_name)
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
    return redirect(url_for('image_format_changer.index'))
