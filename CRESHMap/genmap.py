from . import init_app, db
from .models import (
    Geography,
    GeographyTypes,
    Variables,
    Data
)
#from .models import Variables

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

Layer = namedtuple('Layer', ['gss_code', 'name', 'column_name'])

#LAYERS = {'datazone': Layer('Datazones', "data by Data Zone",
#                            'datazone', 'data'),
#          'westminster_const': Layer('Westminster Constituencies',
#                                     "data by Westminster Constituency",
#                                     'code', 'data_westminster'),
#          'local_authority': Layer('Local Authority',
#                                   "Data by Local Authority",
#                                   'code', 'data_local_authority')}


def main():  # noqa C901
    parser = argparse.ArgumentParser()
    parser.add_argument('config', help="the name of the configuration file")
    parser.add_argument('-o', '--output', metavar='DIR', type=Path,
                        help='write output to DIR')
    args = parser.parse_args()

    cfg = configparser.ConfigParser()
    cfg.read(args.config)

    app = init_app()

    popup_base_name = Path('popup.js')
    quotes_base_name = Path('quotes.js')
    quotes_icon_base_name = Path('chat-left-dots-fill.svg')
    camera_icon_base_name = Path('camera-fill.svg')
    if args.output is not None:
        popup_name = args.output / popup_base_name
    else:
        popup_name = popup_base_name

    with app.app_context():

        if db.engine.url.drivername != 'postgresql':
            print('Error, need a postgres database')
            sys.exit(1)

        layers = {}
        for geo_type in db.session.query(GeographyTypes):
            layers[geo_type.gss_code] = Layer(
                geo_type.name,
                geo_type.name,
                geo_type.column_name
            )

        attributes = {} # TODO: Refactor to variables
        query = db.session.query(
            Variables,
            Data.year,
            func.max(Data.value)
        ).join(Data).group_by(Variables.id, Data.year)
        for a, year, v_max in query:

            index = a.id + '_' + str(year)
            attributes[index] = {}
            attributes[index]['year'] = year
            attributes[index]['id'] = a.id
            for k in ['name', 'start', 'end',
                      'start_colour', 'end_colour']:
                if not a.id in cfg.keys() or k not in cfg[a.id]:
                    if k == 'name':
                        v = a.variable
                    elif k == 'end':
                        v = v_max
                    else:
                        v = ATTRIBUTE_DEFAULTS[k]
                else:
                    v = cfg[a.id][k]
                attributes[index][k] = v

        if len(attributes) == 0:
            print('Error, no attribures specified')
            sys.exit(1)

        bbox = db.session.query(Geography.geometry.ST_Extent()).one()[0]
        try:
            bbox = wkb.loads(bytes(bbox.data)).bounds
        except Exception:
            bb = []
            for pnt in bbox[4:-1].split(','):
                bb += pnt.split()
            bbox = bb

        print(db.engine.url)
        cresh_map = render_template(
            'cresh.map',
            bbox=bbox,
            mapserverurl=app.config['MAPSERVER_URL'],
            dburl=db.engine.url,
            attributes=attributes,
            popup=popup_base_name,
            layers=layers,
            quotes_template=quotes_base_name,
            quotes_icon_name=quotes_icon_base_name,
            camera_icon_name=camera_icon_base_name,
        )
        popup = render_template(str(popup_base_name), attributes=attributes)

        if args.output is not None:
            with (args.output / cfg['setup']['mapfilename']).open('w') as out:
                out.write(cresh_map)
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
