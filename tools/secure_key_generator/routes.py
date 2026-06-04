"""Secure Key Generator — placeholder (not implemented yet)."""
from flask import Blueprint, render_template

bp = Blueprint('secure_key_generator', __name__, url_prefix='/security/key-generator')


@bp.route('/')
def index():
    return render_template('placeholder.html', tool_name='Secure Key Generator')
