"""PDF Password Guard — placeholder (not implemented yet)."""
from flask import Blueprint, render_template

bp = Blueprint('pdf_password_guard', __name__, url_prefix='/pdf/password-guard')


@bp.route('/')
def index():
    return render_template('placeholder.html', tool_name='PDF Password Guard')
