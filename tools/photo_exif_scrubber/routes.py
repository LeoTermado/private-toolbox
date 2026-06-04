"""Photo EXIF Scrubber — placeholder (not implemented yet)."""
from flask import Blueprint, render_template

bp = Blueprint('photo_exif_scrubber', __name__, url_prefix='/image/exif-scrubber')


@bp.route('/')
def index():
    return render_template('placeholder.html', tool_name='Photo EXIF Scrubber')
