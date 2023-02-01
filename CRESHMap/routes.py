from functools import lru_cache
from flask import render_template
from flask_flatpages import FlatPages
from flask import current_app as app
from flask import json
from flask import abort
from sqlalchemy import func
from collections import namedtuple
import numpy
from .models import GeographyTypes
from .models import Variables
from .models import Data

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
    variables = {}
    query = db.session.query(
        Variables,
        Data.year
    ).join(Data).group_by(Variables.id, Data.year).order_by(
        Variables.domain,
        Variables.id,
        Data.year
    )

    for v, year in query:
        index = v.id + '_' + str(year)
        # Get all populated geography types for this variable/year.
        gss_codes = db.session.query(
            func.substr(Data.gss_id, 1, 3).label("gss_code"),
        ).where(
            Data.variable_id == v.id,
            Data.year == year
        ).group_by("gss_code").subquery()

        data_zones = db.session.query(
            GeographyTypes.name
        ).where(
            GeographyTypes.gss_code == gss_codes.c.gss_code
        ).all()

        data_zones = [dz[0] for dz in data_zones]

        variables[index] = {
            'id': v.id,
            'name': f'{v.domain}|{v.variable} ({year})',
            #'name': f'{v.variable} ({year})',
            'description': v.description.replace('\n', ''),
            'year': year,
            'data_zones': data_zones,
        }
    return render_template(
        'map.html', mapserverurl=app.config['MAPSERVER_URL'],
        navigation=menu_items(), variables=variables)


@app.route('/<path:path>')
def page(path):
    page = pages.get_or_404(path)
    return render_template('page.html', page=page, navigation=menu_items())


@app.route('/histogram/<gss_code>/<variable_id>/<year>')
@lru_cache()
def histogram(gss_code, variable_id, year):

    q = db.session.query(getattr(Data, 'value')).filter(
        Data.gss_id.like(gss_code + '%'),
        Data.variable_id == variable_id,
        Data.year == year,
        Data.value >= 0,
    ).all()

    if len(q) == 0:
        result = {'x': [0]*10, 'y': [0]*10}

    else:
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
    response.headers.add('Access-Control-Allow-Origin', '*'),
    return response
