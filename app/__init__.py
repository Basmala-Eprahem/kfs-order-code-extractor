import os
from flask import Flask
import config


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["UPLOAD_DIR"] = config.UPLOAD_DIR
    app.config["PREVIEW_DIR"] = os.path.join(config.OUTPUT_DIR, "previews")
    app.config["DEBUG"] = config.DEBUG

    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    os.makedirs(app.config["PREVIEW_DIR"], exist_ok=True)
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    os.makedirs(config.BATCH_DIR, exist_ok=True)
    os.makedirs(config.JOB_DIR, exist_ok=True)

    from app.routes import bp
    app.register_blueprint(bp)
    return app