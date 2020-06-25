"""App configuration."""
from os import environ
import redis


class Config:
    """Set Flask configuration vars from .env file."""

    # General Config
    SECRET_KEY = environ.get('SECRET_KEY')
    FLASK_APP = environ.get('FLASK_APP')
    FLASK_ENV = environ.get('FLASK_ENV')

    # Flask-Redis
    REDIS_URL = environ.get('REDIS_URL')

    ACCESS_TOKEN = environ.get('ACCESS_TOKEN')
    VERIFY_TOKEN = environ.get('VERIFY_TOKEN')

    # Dropbox
    DROPBOX_ACCESS_TOKEN = environ.get('DROPBOX_ACCESS_TOKEN')

    SUBSCRIPTION_KEY = environ.get('SUBSCRIPTION_KEY')
    ENDPOINT = environ.get('ENDPOINT')

