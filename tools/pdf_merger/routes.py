"""PDF Merger — placeholder (not implemented yet)."""
from flask import Blueprint, render_template

bp = Blueprint('pdf_merger', __name__, url_prefix='/pdf/merger')


@bp.route('/')
def index():
    return render_template('placeholder.html', tool_name='PDF Merger')
