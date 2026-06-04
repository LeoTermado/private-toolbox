"""Universal Image Format Changer — placeholder (not implemented yet)."""
from flask import Blueprint, render_template

bp = Blueprint('image_format_changer', __name__, url_prefix='/image/format-changer')


@bp.route('/')
def index():
    return render_template('placeholder.html', tool_name='Universal Image Format Changer')
