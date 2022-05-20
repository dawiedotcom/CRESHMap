import os


class Config:
    """Set Flask config variables."""

    FLASK_ENV = 'development'
    TESTING = True
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'not-so-secret'
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'

    FLATPAGES_EXTENSION = '.md'
    FLATPAGES_ROOT = 'pages'
