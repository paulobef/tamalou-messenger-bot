release: ./scripts/messenger_settings.sh
web: gunicorn -b :$PORT --chdir flaskr __init__:create_app