from flask import Blueprint

service_management_bp = Blueprint('service_management', __name__, template_folder='templates', static_folder='static')

from . import routes