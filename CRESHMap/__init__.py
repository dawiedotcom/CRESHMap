"""Initialize Flask app."""
from flask import Flask
from flask_flatpages import FlatPages

pages = FlatPages()


def init_app():
    """Construct core Flask application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')

    with app.app_context():
        # Import parts of our core Flask app
        from . import routes  # noqa F401

        # Import Dash application
        from .dash.dashboard import init_dashboard
        app = init_dashboard(app)

        pages.init_app(app)
        return app
