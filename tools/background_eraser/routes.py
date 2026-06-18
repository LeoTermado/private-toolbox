"""Automated Asset Background Eraser blueprint — make a solid background transparent."""
import os

from flask import Blueprint, render_template, request, flash, redirect, url_for, abort

from core.file_utils import archive_session
from core.downloads import send_file_download
from core.validators import has_allowed_extension
from core.file_size import compare_files
from . import service

bp = Blueprint('background_eraser', __name__, url_prefix='/image/background-eraser')


@bp.route('/')
def index():
    return render_template('background_eraser.html', result=None,
                           bg_choices=service.BG_CHOICES, selected_bg=service.DEFAULT_BG,
                           tolerance=service.DEFAULT_TOLERANCE)


@bp.route('/remove', methods=['POST'])
def remove():
    file = request.files.get('file')
    bg_choice = request.form.get('bg_choice', service.DEFAULT_BG)
    tolerance = service.clamp_tolerance(request.form.get('tolerance', service.DEFAULT_TOLERANCE))

    if file is None or file.filename == '':
        flash("Please select an image.")
        return redirect(url_for('background_eraser.index'))

    if not has_allowed_extension(file.filename, service.INPUT_EXTENSIONS):
        flash("Unsupported image type. Use PNG, JPG, WEBP, BMP, GIF or TIFF.")
        return redirect(url_for('background_eraser.index'))

    if bg_choice not in {c[0] for c in service.BG_CHOICES}:
        bg_choice = service.DEFAULT_BG

    try:
        input_path = service.save_upload(file)
        output_path, stats = service.remove_background(input_path, bg_choice, tolerance)
    except Exception:
        flash("Could not process this image. It may be corrupt or unsupported.")
        return redirect(url_for('background_eraser.index'))

    sizes = compare_files(input_path, output_path)
    view = {
        "download_name": os.path.basename(output_path),
        "removed_percent": stats["percent"],
        "color": stats["color"],
        "original_human": sizes["original_human"],
        "output_human": sizes["output_human"],
        "nothing_removed": stats["removed"] == 0,
    }
    return render_template('background_eraser.html', result=view,
                           bg_choices=service.BG_CHOICES, selected_bg=bg_choice,
                           tolerance=tolerance)


@bp.route('/download/<path:filename>')
def download(filename):
    safe_name = os.path.basename(filename)
    path = os.path.join(service.BG_OUTPUT, safe_name)
    if not os.path.isfile(path):
        abort(404)
    return send_file_download(path, download_name=safe_name, mimetype="image/png")


@bp.route('/archive', methods=['POST'])
def archive():
    archive_name = archive_session()
    if archive_name is None:
        flash("Nothing to archive! Input and Output folders are already empty.")
    else:
        flash(f"Successfully archived session into old/{archive_name}/ !")
    return redirect(url_for('background_eraser.index'))
