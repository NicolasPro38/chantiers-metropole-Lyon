from flask import Flask
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

def create_app():
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    app.secret_key = config.SECRET_KEY

    from app.routes import bp
    app.register_blueprint(bp)

    return app
