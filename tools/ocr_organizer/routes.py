"""OCR Organizer — placeholder (not implemented yet)."""
from flask import Blueprint, render_template

bp = Blueprint('ocr_organizer', __name__, url_prefix='/ocr/organizer')


@bp.route('/')
def index():
    return render_template('placeholder.html', tool_name='OCR Organizer')
