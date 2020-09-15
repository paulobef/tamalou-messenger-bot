"""App configuration."""
import os
from dotenv import load_dotenv

load_dotenv('.env')


class Config:
    """Set Flask configuration vars from .env file."""

    # General Config
    SECRET_KEY = os.environ.get('SECRET_KEY')
    FLASK_APP = os.environ.get('FLASK_APP')
    FLASK_ENV = os.environ.get('FLASK_ENV')

    # Flask-Redis
    REDIS_URL = os.environ.get('REDIS_URL')

    ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
    VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')

    # Dropbox
    DROPBOX_ACCESS_TOKEN = os.environ.get('DROPBOX_ACCESS_TOKEN')

    SUBSCRIPTION_KEY = os.environ.get('SUBSCRIPTION_KEY')
    ENDPOINT = os.environ.get('ENDPOINT')

