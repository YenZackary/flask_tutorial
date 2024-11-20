from flask import Flask
from app.monitor import monitor_bp
from app.permission_management import permission_management_bp
from app.service_management import service_management_bp
from app.user_management import user_management_bp


def create_app():
    app = Flask(__name__)
    app.secret_key = 'your_secret_key'
    app.register_blueprint(monitor_bp, url_prefix='/monitor')
    app.register_blueprint(permission_management_bp, url_prefix='/permission_management')
    app.register_blueprint(service_management_bp, url_prefix='/service_management')
    app.register_blueprint(user_management_bp, url_prefix='/user_management')

    return app