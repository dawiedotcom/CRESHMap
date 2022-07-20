import os
from pathlib import Path

basedir = Path(__file__).parent.absolute()


class Config:
    """Set Flask config variables."""

    FLASK_ENV = 'development'
    TESTING = True
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'not-so-secret'
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{basedir}/app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    FLATPAGES_EXTENSION = '.md'
    FLATPAGES_ROOT = 'pages'

    MAPSERVER_URL = os.environ.get('MAPSERVER_URL') or \
        'https://www.geos.ed.ac.uk/maps/mhagdorn/cresh?'
