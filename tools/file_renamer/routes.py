"""File Renamer blueprint — batch-rename uploaded files and download as a ZIP."""
import os

from flask import Blueprint, render_template, request, flash, redirect, url_for, abort

from core.file_utils import archive_session
from core.downloads import send_file_download
from core.validators import filter_nonempty_uploads, validate_upload_count
from . import service

bp = Blueprint('file_renamer', __name__, url_prefix='/files/renamer')


@bp.route('/')
def index():
    return render_template('file_renamer.html', result=None,
                           modes=service.MODE_CHOICES, selected_mode=service.DEFAULT_MODE)


@bp.route('/rename', methods=['POST'])
def rename():
    files = filter_nonempty_uploads(request.files.getlist('files'))
    mode = request.form.get('mode', service.DEFAULT_MODE)
    base_name = request.form.get('base_name', '').strip()
    prefix = request.form.get('prefix', '').strip()
    suffix = request.form.get('suffix', '').strip()

    try:
        start = int(request.form.get('start', '1'))
    except (TypeError, ValueError):
        start = 1

    # --- Validation ---
    if not validate_upload_count(files, min_count=1):
        flash("Please select at least one file to rename.")
        return redirect(url_for('file_renamer.index'))

    if mode not in {m[0] for m in service.MODE_CHOICES}:
        mode = service.DEFAULT_MODE

    if mode == "sequence" and not base_name:
        flash("Please enter a base name for sequential numbering.")
        return redirect(url_for('file_renamer.index'))

    if mode == "prefix_suffix" and not prefix and not suffix:
        flash("Please enter a prefix and/or a suffix.")
        return redirect(url_for('file_renamer.index'))

    # --- Rename ---
    try:
        input_paths = service.save_uploads(files)
        plan = service.plan_names(input_paths, mode, base_name=base_name,
                                  prefix=prefix, suffix=suffix, start=start)
        out_paths = service.apply_renames(plan)
        zip_path = service.build_zip(out_paths)
    except Exception:
        flash("Could not rename these files. Please try again.")
        return redirect(url_for('file_renamer.index'))

    view = {
        "rows": [{"old": os.path.basename(src), "new": new} for src, new in plan],
        "zip_name": os.path.basename(zip_path),
        "count": len(plan),
    }
    return render_template('file_renamer.html', result=view,
                           modes=service.MODE_CHOICES, selected_mode=mode)


@bp.route('/download/<path:filename>')
def download(filename):
    safe_name = os.path.basename(filename)
    path = os.path.join(service.RENAMER_OUTPUT, safe_name)
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
    return redirect(url_for('file_renamer.index'))
