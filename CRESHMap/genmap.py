from . import init_app, db
from .models import (
    Geography,
    GeographyTypes,
    Variables,
    Data
)

from collections import namedtuple
from pathlib import Path
import configparser
from flask import render_template
from shapely import wkb
import argparse
import sys
import shutil
from sqlalchemy.sql.expression import func


ATTRIBUTE_DEFAULTS = {
    'start': 0,
    'start_colour': "0 255 0",
    'end_colour': "255 0 0"}

Layer = namedtuple('Layer', ['gss_code', 'name', 'column_name', 'variables'])

def get_db_schema(url):
    '''Tries to parse the Postgres schema from the database URL'''
    options = url.query.get('options', None)
    if options is None or not 'search_path=' in options:
        return None
    parts = options.split(' ')
    for part in parts:
        if 'search_path=' in part:
            idx = part.find('search_path=') + len('search_path=')
            return part[idx:]

def main():  # noqa C901
    parser = argparse.ArgumentParser()
    parser.add_argument('config', help="the name of the configuration file")
    parser.add_argument('-o', '--output', metavar='DIR', type=Path,
                        help='write output to DIR')
    args = parser.parse_args()

    cfg = configparser.ConfigParser()
    cfg.read(args.config)

    app = init_app()

    quotes_base_name = Path('quotes.js')
    quotes_icon_base_name = Path('chat-left-dots-fill.svg')
    camera_icon_base_name = Path('camera-fill.svg')

    with app.app_context():

        if db.engine.url.drivername != 'postgresql':
            print('Error, need a postgres database')
            sys.exit(1)

        layers = {}
        for geo_type in db.session.query(GeographyTypes):
            layers[geo_type.gss_code] = Layer(
                geo_type.name,
                geo_type.name,
                geo_type.column_name,
                {}
            )

        query = db.session.query(
            Variables,
            Data.year,
            GeographyTypes.gss_code,
            func.max(Data.value)
        ).where(
            (Variables.id == Data.variable_id) &
            (func.substr(Data.gss_id, 1, 3) == GeographyTypes.gss_code)
        ).group_by(
            Variables.id,
            Data.year,
            GeographyTypes.gss_code
        )
        for variable, year, gss_code, v_max in query:

            index = variable.id + '_' + str(year)
            layers[gss_code].variables[index] = {}
            layers[gss_code].variables[index]['year'] = year
            layers[gss_code].variables[index]['id'] = variable.id
            for key in ['name', 'start', 'end',
                      'start_colour', 'end_colour']:
                if not variable.id in cfg.keys() or key not in cfg[variable.id]:
                    if key == 'name':
                        value = variable.variable
                    elif key == 'end':
                        value = v_max
                    else:
                        value = ATTRIBUTE_DEFAULTS[key]
                else:
                    value = cfg[variable.id][key]
                layers[gss_code].variables[index][key] = value

        # Filter layers with no data
        layers = {layer_name : layer for layer_name, layer in layers.items() if len(layer.variables) > 0}

        bbox = db.session.query(Geography.geometry.ST_Extent()).one()[0]
        try:
            bbox = wkb.loads(bytes(bbox.data)).bounds
        except Exception:
            bb = []
            for pnt in bbox[4:-1].split(','):
                bb += pnt.split()
            bbox = bb

        print(db.engine.url)
        db_schema = get_db_schema(db.engine.url)
        db_schema_clause = db_schema.split(',')[0] + '.' if db_schema else ''
        print(f'db_schema={db_schema} db_schema_clause={db_schema_clause}')
        cresh_map = render_template(
            'cresh.map',
            bbox=bbox,
            mapserverurl=app.config['MAPSERVER_URL'],
            dburl=db.engine.url,
            db_schema_clause=db_schema_clause,
            layers=layers,
            quotes_template=quotes_base_name,
            quotes_icon_name=quotes_icon_base_name,
            camera_icon_name=camera_icon_base_name,
        )

        if args.output is not None:
            with (args.output / cfg['setup']['mapfilename']).open('w') as out:
                out.write(cresh_map)

            for layer_name, layer in layers.items():
                popup = render_template('popup.js', attributes=layer.variables)

                popup_base_name = Path(f'popup_{layer_name}.js')
                popup_name = args.output / popup_base_name
                with (popup_name).open('w') as out:
                    out.write(popup)

            shutil.copy(
                str(Path('CRESHMap/templates') / quotes_base_name),
                str(args.output / quotes_base_name)
            )
            shutil.copy(
                str(Path('CRESHMap/static/images') / quotes_icon_base_name),
                str(args.output / quotes_icon_base_name)
            )
            shutil.copy(
                str(Path('CRESHMap/static/images') / camera_icon_base_name),
                str(args.output / camera_icon_base_name)
            )
        else:
            print(cresh_map)
            print(popup)


if __name__ == '__main__':
    main()
