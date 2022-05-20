from flask import render_template
from flask_flatpages import FlatPages
from flask import current_app as app

pages = FlatPages(app)


@app.route('/')
def home():
    """Landing page."""

    return render_template('index.html', who='magi')


@app.route('/<path:path>')
def page(path):
    page = pages.get_or_404(path)
    return render_template('page.html', page=page)
