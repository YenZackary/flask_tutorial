from flask import Blueprint

permission_management_bp = Blueprint('permission_management', __name__, template_folder='templates', static_folder='static')

from . import routes