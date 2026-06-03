"""Image to PDF — placeholder (not implemented yet)."""
from flask import Blueprint, render_template

bp = Blueprint('image_to_pdf', __name__, url_prefix='/image/to-pdf')


@bp.route('/')
def index():
    return render_template('placeholder.html', tool_name='Image to PDF')
