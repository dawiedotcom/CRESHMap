from functools import lru_cache
from flask import render_template
from flask_flatpages import FlatPages
from flask import current_app as app
from flask import json
from flask import abort
from sqlalchemy import func
from collections import namedtuple
import numpy
import pandas
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
@lru_cache()
def index():
    selection = {}

    domains = db.session.query(
        Variables.domain,
    ).group_by(
        Variables.domain,
    ).order_by(
        Variables.domain,
    )

    for domain, in domains:
        selection[domain] = {}

        variables = db.session.query(
            Variables,
        ).where(
            Variables.domain == domain,
        ).group_by(Variables.id).order_by(
            Variables.id,
        ).order_by(
            Variables.variable,
        )

        for v in variables:
            # Get all populated geography types for this variable/year.
            gss_codes = db.session.query(
                func.substr(Data.gss_id, 1, 3).label("gss_code"),
            ).where(
                Data.variable_id == v.id,
                #Data.year == year
            ).group_by("gss_code").subquery()
            
            data_zones = db.session.query(
                GeographyTypes.name,
                GeographyTypes.gss_code
            ).where(
                GeographyTypes.gss_code == gss_codes.c.gss_code
            ).order_by(
                GeographyTypes.gss_code,
            ).all()
            data_zones = [{'name': dz[0], 'gss_code': dz[1]} for dz in data_zones]

            # Skip variables with no data 
            if (len(data_zones) == 0):
                continue

            selection[domain][v.id] = {
                'id': v.id,
                'name': v.variable,
                'domain': v.domain,
                'description': v.description.replace('\n', ''),
                'data_zones': [],
                'id_year': {},
                'year_id': {},
            }

            years = db.session.query(
                Data.year
            ).group_by(Data.year).where(
                Data.variable_id == v.id
            ).all()
            years = [y[0] for y in years]

            for year in years:
                index = f'{v.id}_{year}'
                selection[domain][v.id]['id_year'][year] = index
                selection[domain][v.id]['year_id'][index] = year

            selection[domain][v.id]['data_zones'] = data_zones

        if selection[domain] == {}:
            selection.pop(domain)

    domains = selection.keys()

    mapattribs = json.dumps(selection, indent=2)

    return render_template(
        'map.html',
        mapserverurl=app.config['MAPSERVER_URL'],
        navigation=menu_items(),
        mapattribs=mapattribs,
        domains=domains,
        years=years,
    )


@app.route('/<path:path>')
def page(path):
    page = pages.get_or_404(path)
    return render_template('page.html', page=page, navigation=menu_items())


def select_values(gss_code, variable_id, year):
    return db.session.query(getattr(Data, 'value')).filter(
        Data.gss_id.like(gss_code + '%'),
        Data.variable_id == variable_id,
        Data.year == year,
        Data.value >= 0,
    ).all()


def make_json_response(data):
    response = app.response_class(
        response=json.dumps(data),
        status=200,
        mimetype='application/json',
    )
    response.headers.add('Access-Control-Allow-Origin', '*'),
    return response

@app.route('/histogram/<gss_code>/<variable_id>/<year>')
@lru_cache()
def histogram(gss_code, variable_id, year):

    values = select_values(gss_code, variable_id, year)

    if len(values) == 0:
        return make_json_response({'x': [0]*10, 'y': [0]*10})

    data = numpy.array(values)[:, 0]
    data = data[~numpy.isnan(data)]
    count, bins = numpy.histogram(data, bins=10)
    xvals = (bins[:-1] + bins[1:]) / 2
    result = {'x': xvals.tolist(), 'y': count.tolist()}

    return make_json_response(result)


@app.route('/quintile/<gss_code>/<variable_id>/<year>')
@lru_cache()
def quintile(gss_code, variable_id, year):

    values = select_values(gss_code, variable_id, year)
    nbins = 5

    if len(values) == 0:
        return make_json_response({'bins': [0]*nbins})

    data = numpy.array(values)[:, 0]
    data = data[~numpy.isnan(data)]
    v_min = numpy.max(data[data == data].min(), 0)
    v_max = data[data==data].max()

    try:
        _, bins = pandas.qcut(
            data[(data<=v_max) & (data > v_min)],
            nbins,
            retbins=True,
        )
        bins[0] = v_min
        result = {'bins': bins.tolist()}
    except ValueError:
        result = {'bins':[0]*nbins}

    return make_json_response(result)
