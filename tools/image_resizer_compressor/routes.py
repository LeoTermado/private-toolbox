"""Image Resizer & Compressor — placeholder (not implemented yet)."""
from flask import Blueprint, render_template

bp = Blueprint('image_resizer_compressor', __name__, url_prefix='/image/resizer-compressor')


@bp.route('/')
def index():
    return render_template('placeholder.html', tool_name='Image Resizer & Compressor')
