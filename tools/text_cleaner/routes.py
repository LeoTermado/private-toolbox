"""Text Cleaner — placeholder (not implemented yet)."""
from flask import Blueprint, render_template

bp = Blueprint('text_cleaner', __name__, url_prefix='/text/cleaner')


@bp.route('/')
def index():
    return render_template('placeholder.html', tool_name='Text Cleaner')
