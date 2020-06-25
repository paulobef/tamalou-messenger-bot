from flask import Flask
from flask_redis import FlaskRedis

from flaskr.utils.dropbox_connector import DropboxConnector

redis_client = FlaskRedis(decode_responses=True)


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    from config import Config
    app.config.from_object(Config)
    with app.app_context():
        from .conversation.route import conversation
        app.register_blueprint(conversation)
        redis_client.init_app(app)  # Initializing our Flask application

        return app
