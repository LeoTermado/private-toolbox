"""ZIP Splitter — placeholder (not implemented yet)."""
from flask import Blueprint, render_template

bp = Blueprint('zip_splitter', __name__, url_prefix='/files/zip-splitter')


@bp.route('/')
def index():
    return render_template('placeholder.html', tool_name='ZIP Splitter')
