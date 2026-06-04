"""Automated Asset Background Eraser — placeholder (not implemented yet)."""
from flask import Blueprint, render_template

bp = Blueprint('background_eraser', __name__, url_prefix='/image/background-eraser')


@bp.route('/')
def index():
    return render_template('placeholder.html', tool_name='Automated Asset Background Eraser')
