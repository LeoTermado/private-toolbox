"""PDF to Image — placeholder (not implemented yet)."""
from flask import Blueprint, render_template

bp = Blueprint('pdf_to_image', __name__, url_prefix='/pdf/to-image')


@bp.route('/')
def index():
    return render_template('placeholder.html', tool_name='PDF to Image')
