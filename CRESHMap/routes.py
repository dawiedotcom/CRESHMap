from flask import render_template
from flask_flatpages import FlatPages
from flask import current_app as app
from collections import namedtuple


pages = FlatPages(app)

MenuItem = namedtuple("MenuItem", "title path order")


def menu_items():
    menu = [MenuItem("Map", "/", 1)]
    for p in pages:
        menu.append(MenuItem(p['title'], p.path, p['order']))
    menu = sorted(menu, key=lambda item: item.order)
    return menu


@app.route('/')
def index():
    return render_template(
        'map.html', mapserverurl=app.config['MAPSERVER_URL'],
        navigation=menu_items())


@app.route('/<path:path>')
def page(path):
    page = pages.get_or_404(path)
    return render_template('page.html', page=page, navigation=menu_items())
