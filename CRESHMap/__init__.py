"""Initialize Flask app."""
from flask import Flask


def init_app():
    """Construct core Flask application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')

    with app.app_context():
        # Import parts of our core Flask app
        from . import routes  # noqa F401

        return app
