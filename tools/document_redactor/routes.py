"""Document Redactor — placeholder (not implemented yet)."""
from flask import Blueprint, render_template

bp = Blueprint('document_redactor', __name__, url_prefix='/privacy/redactor')


@bp.route('/')
def index():
    return render_template('placeholder.html', tool_name='Document Redactor')
