from functools import lru_cache
from flask import render_template
from flask_flatpages import FlatPages
from flask import current_app as app
from flask import json
from flask import abort
from flask import redirect
from flask import request
from flask import session
from flask import url_for
from flask import flash
from flask import send_from_directory
from sqlalchemy import func
from collections import namedtuple
import numpy
import pandas
import random
import re
import hashlib
import datetime
from .models import GeographyTypes
from .models import Variables
from .models import Data
from .models import DownloadLink
from .email import send_download_link

from . import db

pages = FlatPages(app)

MenuItem = namedtuple("MenuItem", "title path order")

def menu_items():
    menu = [
        MenuItem("Map", "/", 1),
        MenuItem("Download", '/download', 2),
    ]
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
        ).filter(
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
            ).filter(
                Data.variable_id == v.id,
                #Data.year == year
            ).group_by("gss_code").subquery()

            data_zones = db.session.query(
                GeographyTypes.name,
                GeographyTypes.gss_code
            ).filter(
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
            ).group_by(Data.year).filter(
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

def is_valid_email(email):
    return not re.fullmatch('.*@.*\..*', email) is None

def is_valid_name(name):
    match = re.findall('((https|http|ftp)*(://)*(\w+\.)+\w+)', name)
    return len(match) == 0

def make_random_hash():
    salt = str(random.randint(0, 1e24))
    m = hashlib.sha256()
    m.update(salt.encode('utf-8'))
    return m.hexdigest()

@app.route('/download', methods=('GET', 'POST'))
def download():
    session['from_download'] = True

    if request.method == 'POST':
        if not session.get('from_download', False):
            # Check that the session visited /download to prevent spam
            return render_template(
                'download.html',
                navigation=menu_items(),
            )

        if not is_valid_email(request.form['email']):
            flash("Please provide a valid email address")
            return render_template(
                'download.html',
                navigation=menu_items(),
            )

        name = request.form['name']
        if name == '':
            flash("Please provide a full name.")
            return render_template(
                'download.html',
                navigation=menu_items(),
            )

        if not is_valid_name(name):
            return render_template(
                'download.html',
                navigation=menu_items(),
            )


        download_links = db.session.query(
            DownloadLink
        ).filter(
            DownloadLink.email == request.form['email']
        ).all()

        if download_links == []:
            # Create a new entry for this email address
            download_link = DownloadLink()
            download_link.email = request.form['email']
            download_link.download_hash = make_random_hash()
            download_link.last_accessed = datetime.datetime(1970, 1, 1)

        else:
            download_link = download_links[0]

        if (not download_link.name == request.form or
            not download_link.organization == request.organization):

            download_link.name = request.form['name']
            download_link.organization = request.form['organization']

            db.session.add(download_link)
            db.session.commit()

        #if app.config['EMAIL_FROM_ADDR'] and app.config['EMAIL_SMTP_SERV']:
        #    send_download_link(
        #        app.config['EMAIL_FROM_ADDR'],
        #        app.config['EMAIL_SMTP_SERV'],
        #        download_link.name,
        #        download_link.email,
        #        download_link.download_hash,
        #        app.config['DOMAIN']
        #    )

        url = 'https://{tldn}/download/{dl_hash}'.format(
            tldn=app.config['DOMAIN'],
            dl_hash=download_link.download_hash,
        )
        flash(f'You can download the data set <a href="{url}" class="alert-link">here</a>', 'success')

    return render_template(
        'download.html',
        navigation=menu_items(),
    )

@app.route('/download/<download_hash>')
def download_data(download_hash):
    download_links = db.session.query(
        DownloadLink
    ).filter(
        DownloadLink.download_hash == download_hash,
    ).all()

    if download_links == []:
        return redirect(url_for('download'))

    # TODO update accessed time in db


    return send_from_directory(
        'data',
        'Creshmap_Dataset_Tobacco_Alcohol.xlsx',
        as_attachment=True,
        attachment_filename='Creshmap_Dataset_Tobacco_Alcohol.xlsx',
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
