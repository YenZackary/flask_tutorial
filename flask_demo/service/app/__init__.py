from flask import Flask
from app.hello import hello_bp
from app.review import review_bp

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your_secret_key'
    app.register_blueprint(hello_bp, url_prefix='/hello')
    app.register_blueprint(review_bp, url_prefix='/review')

    return app