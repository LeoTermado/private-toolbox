"""Archive Content Inspector — placeholder (not implemented yet)."""
from flask import Blueprint, render_template

bp = Blueprint('archive_content_inspector', __name__, url_prefix='/files/archive-inspector')


@bp.route('/')
def index():
    return render_template('placeholder.html', tool_name='Archive Content Inspector')
