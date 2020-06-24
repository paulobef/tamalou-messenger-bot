from flask import Flask
from flask_redis import FlaskRedis

redis_client = FlaskRedis(decode_responses=True)


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    from .config import Config
    app.config.from_object(Config)

    from .conversation.route import conversation
    app.register_blueprint(conversation)
    with app.app_context():
        redis_client.init_app(app)  # Initializing our Flask application

        return app
