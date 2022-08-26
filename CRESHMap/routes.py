from flask import render_template
from flask_flatpages import FlatPages
from flask import current_app as app
from flask import json
from flask import abort
from collections import namedtuple
import numpy
#from .models import Geography
#from .models import Attribute
#from .models import BaseData

from . import db

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
    attributes = {}
    for a in db.session.query(Attribute):
        attributes[a.attribute] = {'name': a.name,
                                   'description': a.description}
    return render_template(
        'map.html', mapserverurl=app.config['MAPSERVER_URL'],
        navigation=menu_items(), attributes=attributes)


@app.route('/<path:path>')
def page(path):
    page = pages.get_or_404(path)
    return render_template('page.html', page=page, navigation=menu_items())


@app.route('/histogram/<geography>/<attribute>')
def histogram(geography, attribute):

    try:
        attrib = getattr(BaseData, attribute)
    except Exception:
        abort(404, f'no such attribute: {attribute}')

    geog = db.session.query(Geography.geography).filter(
        Geography.name == geography)
    q = db.session.query(attrib).filter(
        BaseData.geography.in_(geog)).all()
    if len(q) == 0:
        abort(404, f'no such geography: {geography}')

    data = numpy.array(q)[:, 0]
    data = data[~numpy.isnan(data)]
    count, bins = numpy.histogram(data, bins=10)
    xvals = (bins[:-1] + bins[1:]) / 2
    result = {'x': xvals.tolist(), 'y': count.tolist()}

    response = app.response_class(
        response=json.dumps(result),
        status=200,
        mimetype='application/json'
    )
    return response
