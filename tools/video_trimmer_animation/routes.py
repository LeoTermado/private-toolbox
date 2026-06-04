"""Video Snippet Trimmer & Animation Creator — placeholder (not implemented yet)."""
from flask import Blueprint, render_template

bp = Blueprint('video_trimmer_animation', __name__, url_prefix='/media/video-trimmer')


@bp.route('/')
def index():
    return render_template('placeholder.html', tool_name='Video Snippet Trimmer & Animation Creator')
