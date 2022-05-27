from flask import render_template
from flask_flatpages import FlatPages
from flask import current_app as app
from collections import namedtuple

import pandas
import json
import plotly
import plotly.express as px


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
    df = pandas.DataFrame({
        'city': [
            'Glasgow', 'Edinburgh', 'Aberdeen', 'Dundee', 'Dunfermline',
            'Inverness', 'Perth', 'Stirling'],
        'latitude': [
            55.8642, 55.9533, 57.1499, 56.4620, 56.0717,
            57.4778, 56.3950, 56.1165],
        'longitude': [
            -4.2518, -3.1883, -2.0938, -2.9707, -3.4522,
            -4.2247, -3.4308, -3.9369],
        'size': [632350, 506520, 198590, 148210, 54990, 47790, 47350, 37910]
    })

    fig = px.scatter_mapbox(df, lat='latitude', lon='longitude',
                            color_discrete_sequence=["fuchsia"],
                            hover_name="city", zoom=7,
                            center={'lat': 56.4907, 'lon': -4.2026})
    fig.update_layout(mapbox_style="stamen-toner", autosize=True)

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('map.html', graphJSON=graphJSON,
                           navigation=menu_items())


@app.route('/<path:path>')
def page(path):
    page = pages.get_or_404(path)
    return render_template('page.html', page=page, navigation=menu_items())
