from flask import render_template
from flask_flatpages import FlatPages
from flask import current_app as app

pages = FlatPages(app)


def menu_items():
    menu = []
    for p in pages:
        menu.append((p['title'], p.path))
    return menu


@app.route('/')
def index():
    """Landing page."""

    return render_template('index.html', who='magi', navigation=menu_items())


@app.route('/<path:path>')
def page(path):
    page = pages.get_or_404(path)
    return render_template('page.html', page=page, navigation=menu_items())
