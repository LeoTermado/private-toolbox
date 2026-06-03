"""PDF Compressor — placeholder (not implemented yet)."""
from flask import Blueprint, render_template

bp = Blueprint('pdf_compressor', __name__, url_prefix='/pdf/compressor')


@bp.route('/')
def index():
    return render_template('placeholder.html', tool_name='PDF Compressor')
