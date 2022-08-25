"""Initialize Flask app."""
from flask import Flask, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_flatpages import FlatPages
from flask_flatpages.utils import pygmented_markdown
from sqlalchemy.event import listen
from sqlalchemy.sql import select, func
from sqlalchemy import inspect

from .config import Config

pages = FlatPages()
db = SQLAlchemy()


def renderer(text):
    prerendered_body = render_template_string(text)
    return pygmented_markdown(prerendered_body)


def load_spatialite(dbapi_conn, connection_record):
    dbapi_conn.enable_load_extension(True)
    dbapi_conn.load_extension('/usr/lib/x86_64-linux-gnu/mod_spatialite.so')


def init_app():
    """Construct core Flask application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(Config)
    app.config['FLATPAGES_HTML_RENDERER'] = renderer

    db.init_app(app)

    with app.app_context():
        # Import parts of our core Flask app
        from . import routes  # noqa F401
        if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
            # see https://geoalchemy-2.readthedocs.io/en/latest/spatialite_tutorial.html # noqa: E501
            engine = db.get_engine()
            listen(engine, 'connect', load_spatialite)
            if 'geometry_columns' not in inspect(engine).get_table_names():
                app.logger.info('creating spatial index')
                db.engine.execute(select([func.InitSpatialMetaData(1)]))

        pages.init_app(app)
        return app
