from flask import Flask
from flask_cors import CORS

from .api.routes import api
from .config import Config


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["MAX_CONTENT_LENGTH"] = 4096
    if test_config:
        app.config.update(test_config)
    CORS(app, resources={r"/api/*": {"origins": app.config["FRONTEND_ORIGINS"]}})
    app.register_blueprint(api, url_prefix="/api/v1")
    return app
