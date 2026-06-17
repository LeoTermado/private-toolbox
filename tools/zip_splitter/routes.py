"""ZIP Splitter blueprint — split a ZIP into smaller ZIP parts."""
import os

from flask import Blueprint, render_template, request, flash, redirect, url_for, abort

from core.file_utils import archive_session
from core.downloads import send_file_download
from core.validators import has_allowed_extension
from core.file_size import format_file_size
from . import service

bp = Blueprint('zip_splitter', __name__, url_prefix='/files/zip-splitter')


@bp.route('/')
def index():
    return render_template('zip_splitter.html', result=None, default_max_mb=service.DEFAULT_MAX_MB)


@bp.route('/split', methods=['POST'])
def split():
    file = request.files.get('file')
    max_mb = service.clamp_max_mb(request.form.get('max_mb', service.DEFAULT_MAX_MB))

    if file is None or file.filename == '':
        flash("Please select a ZIP file to split.")
        return redirect(url_for('zip_splitter.index'))

    if not has_allowed_extension(file.filename, service.ALLOWED_EXTENSIONS):
        flash("Only .zip archives are supported.")
        return redirect(url_for('zip_splitter.index'))

    try:
        input_path = service.save_upload(file)
        part_infos, bundle_path = service.split_zip(input_path, max_mb)
    except ValueError as exc:
        flash(str(exc))
        return redirect(url_for('zip_splitter.index'))
    except Exception:
        flash("Could not split this archive. It may be corrupt or unsupported.")
        return redirect(url_for('zip_splitter.index'))

    view = {
        "max_mb": max_mb,
        "part_count": len(part_infos),
        "parts": [
            {"name": p["name"], "file_count": p["file_count"],
             "size_human": format_file_size(p["size_bytes"])}
            for p in part_infos
        ],
        "bundle_name": os.path.basename(bundle_path),
    }
    return render_template('zip_splitter.html', result=view, default_max_mb=max_mb)


@bp.route('/download/<path:filename>')
def download(filename):
    safe_name = os.path.basename(filename)
    path = os.path.join(service.ZIP_OUTPUT, safe_name)
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
    return redirect(url_for('zip_splitter.index'))
