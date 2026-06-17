"""Archive Content Inspector blueprint — list the contents of a ZIP/TAR archive."""
from flask import Blueprint, render_template, request, flash, redirect, url_for

from core.file_utils import archive_session
from core.validators import has_allowed_extension
from core.file_size import format_file_size
from . import service

bp = Blueprint('archive_content_inspector', __name__, url_prefix='/files/archive-inspector')


@bp.route('/')
def index():
    return render_template('archive_content_inspector.html', result=None)


@bp.route('/inspect', methods=['POST'])
def inspect():
    file = request.files.get('file')

    if file is None or file.filename == '':
        flash("Please select an archive file to inspect.")
        return redirect(url_for('archive_content_inspector.index'))

    if not has_allowed_extension(file.filename, service.ALLOWED_EXTENSIONS):
        flash("Unsupported file type. Please upload a .zip or .tar archive.")
        return redirect(url_for('archive_content_inspector.index'))

    try:
        path = service.save_upload(file)
        summary = service.inspect_archive(path)
    except ValueError as exc:
        flash(str(exc))
        return redirect(url_for('archive_content_inspector.index'))
    except Exception:
        flash("Could not read this archive. It may be corrupt or unsupported.")
        return redirect(url_for('archive_content_inspector.index'))

    entries = summary["entries"]
    truncated = len(entries) > service.MAX_ENTRIES
    shown = entries[:service.MAX_ENTRIES]

    view = {
        "type": summary["type"],
        "file_count": summary["file_count"],
        "total_human": format_file_size(summary["total_bytes"]),
        "compressed_human": (format_file_size(summary["compressed_bytes"])
                             if summary["compressed_bytes"] is not None else None),
        "ratio": summary["ratio"],
        "truncated": truncated,
        "shown_count": len(shown),
        "entries": [
            {
                "name": e["name"],
                "size_human": format_file_size(e["size"]),
                "compressed_human": (format_file_size(e["compressed"])
                                     if e["compressed"] is not None else "—"),
                "modified": e["modified"] or "—",
            }
            for e in shown
        ],
    }
    return render_template('archive_content_inspector.html', result=view)


@bp.route('/archive', methods=['POST'])
def archive():
    archive_name = archive_session()
    if archive_name is None:
        flash("Nothing to archive! Input and Output folders are already empty.")
    else:
        flash(f"Successfully archived session into old/{archive_name}/ !")
    return redirect(url_for('archive_content_inspector.index'))
