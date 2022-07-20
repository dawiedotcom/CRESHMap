from . import init_app, db
from .models import DataZone, Data

from collections import namedtuple
from pathlib import Path
import configparser
from flask import render_template
from shapely import wkb
import argparse
import sys


ATTRIBUTE_DEFAULTS = {
    'start': 0,
    'start_colour': "0 255 0",
    'end_colour': "255 0 0"}

Layer = namedtuple('Layer', ['title', 'abstract', 'id', 'table'])

LAYERS = {'datazone': Layer('Datazones', "data by Data Zone",
                            'datazone', 'data'),
          'westminster_const': Layer('Westminster Constituencies',
                                     "data by Westminster Constituency",
                                     'code', 'data_westminster'),
          'local_authority': Layer('Local Authority',
                                   "Data by Local Authority",
                                   'code', 'data_local_authority')}


def main():  # noqa C901
    parser = argparse.ArgumentParser()
    parser.add_argument('config', help="the name of the configuration file")
    parser.add_argument('-o', '--output', metavar='DIR', type=Path,
                        help='write output to DIR')
    args = parser.parse_args()

    cfg = configparser.ConfigParser()
    cfg.read(args.config)

    app = init_app()

    popup_name = Path('popup.html')
    if args.output is not None:
        popup_name = args.output / popup_name

    with app.app_context():

        if db.engine.url.drivername != 'postgresql':
            print('Error, need a postgres database')
            sys.exit(1)

        attributes = {}
        for a in cfg.keys():
            if a in ['setup', 'DEFAULT']:
                continue

            if not hasattr(Data, a):
                print(f'Error, unknown attribute {a}')
                sys.exit(1)

            attributes[a] = {}
            for k in ['name', 'start', 'end',
                      'start_colour', 'end_colour']:
                if k not in cfg[a]:
                    if k == 'name':
                        v = a
                    elif k == 'end':
                        col = getattr(Data, a)
                        v = db.session.query(
                            db.func.max(col)).filter(col != 'NaN').one()[0]
                    else:
                        v = ATTRIBUTE_DEFAULTS[k]
                else:
                    v = cfg[a][k]
                attributes[a][k] = v

        if len(attributes) == 0:
            print('Error, no attribures specified')
            sys.exit(1)

        bbox = db.session.query(DataZone.geometry.ST_Extent()).one()[0]
        try:
            bbox = wkb.loads(bytes(bbox.data)).bounds
        except Exception:
            bb = []
            for pnt in bbox[4:-1].split(','):
                bb += pnt.split()
            bbox = bb

        cresh_map = render_template(
            'cresh.map', bbox=bbox,
            mapserverurl=app.config['MAPSERVER_URL'], dburl=db.engine.url,
            attributes=attributes, popup=popup_name, layers=LAYERS)
        popup = render_template('popup.html', attributes=attributes)

        if args.output is not None:
            with (args.output / cfg['setup']['mapfilename']).open('w') as out:
                out.write(cresh_map)
            with (popup_name).open('w') as out:
                out.write(popup)
        else:
            print(cresh_map)
            print(popup)


if __name__ == '__main__':
    main()
