from flask import Blueprint

review_bp = Blueprint('review', __name__, template_folder='templates', static_folder='static')

from . import routes