"""Audio & Video Converter — placeholder (not implemented yet)."""
from flask import Blueprint, render_template

bp = Blueprint('media_converter', __name__, url_prefix='/media/converter')


@bp.route('/')
def index():
    return render_template('placeholder.html', tool_name='Audio & Video Converter')
