"""File Checksum Generator — placeholder (not implemented yet)."""
from flask import Blueprint, render_template

bp = Blueprint('file_checksum_generator', __name__, url_prefix='/files/checksum')


@bp.route('/')
def index():
    return render_template('placeholder.html', tool_name='File Checksum Generator')
