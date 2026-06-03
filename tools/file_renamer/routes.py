"""File Renamer — placeholder (not implemented yet)."""
from flask import Blueprint, render_template

bp = Blueprint('file_renamer', __name__, url_prefix='/files/renamer')


@bp.route('/')
def index():
    return render_template('placeholder.html', tool_name='File Renamer')
