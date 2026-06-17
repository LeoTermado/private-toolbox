"""Photo EXIF Scrubber blueprint — remove EXIF/metadata from an image."""
import mimetypes
import os

from flask import Blueprint, render_template, request, flash, redirect, url_for, abort

from core.file_utils import archive_session
from core.downloads import send_file_download
from core.validators import has_allowed_extension
from core.file_size import compare_files
from . import service

bp = Blueprint('photo_exif_scrubber', __name__, url_prefix='/image/exif-scrubber')


@bp.route('/')
def index():
    return render_template('photo_exif_scrubber.html', result=None)


@bp.route('/scrub', methods=['POST'])
def scrub():
    file = request.files.get('file')

    if file is None or file.filename == '':
        flash("Please select an image.")
        return redirect(url_for('photo_exif_scrubber.index'))

    if not has_allowed_extension(file.filename, service.INPUT_EXTENSIONS):
        flash("Unsupported image type. Use PNG, JPG, WEBP, BMP, GIF or TIFF.")
        return redirect(url_for('photo_exif_scrubber.index'))

    try:
        input_path = service.save_upload(file)
        output_path, exif_count = service.scrub(input_path)
    except Exception:
        flash("Could not process this image. It may be corrupt or unsupported.")
        return redirect(url_for('photo_exif_scrubber.index'))

    sizes = compare_files(input_path, output_path)
    view = {
        "download_name": os.path.basename(output_path),
        "exif_count": exif_count,
        "had_exif": exif_count > 0,
        "original_human": sizes["original_human"],
        "output_human": sizes["output_human"],
    }
    return render_template('photo_exif_scrubber.html', result=view)


@bp.route('/download/<path:filename>')
def download(filename):
    safe_name = os.path.basename(filename)
    path = os.path.join(service.EXIF_OUTPUT, safe_name)
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
    return redirect(url_for('photo_exif_scrubber.index'))
