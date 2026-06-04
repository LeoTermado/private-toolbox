"""PDF Metadata Purge — placeholder (not implemented yet)."""
from flask import Blueprint, render_template

bp = Blueprint('pdf_metadata_purge', __name__, url_prefix='/pdf/metadata-purge')


@bp.route('/')
def index():
    return render_template('placeholder.html', tool_name='PDF Metadata Purge')
