from CRESHMap import init_app, db
from CRESHMap.models import Attribute
from CRESHMap.models import DataZone
from CRESHMap.models import WestminsterConstituency
from CRESHMap.models import LocalAuthority
from CRESHMap.models import Data
from CRESHMap.models import DataWestminster
from CRESHMap.models import DataLocalAuthority

from collections import namedtuple
import argparse
import fiona
from shapely.geometry import shape
from shapely.ops import transform
import pyproj

from pathlib import Path
import configparser
import pandas
import markdown
import sys


DB_PROJECTION = pyproj.CRS('EPSG:4326')

MAPPING = {2020: {
    "Data_Zone": "datazone_id",
    "Total_population": "total_population",
    "ALCOHOL": "alcohol",
    "DRUG": "drug"}}

Geography = namedtuple('Geography', ['cls', 'dbid', 'id', 'name'])

GEOGRAPHIES = {
    'D': Geography(DataZone, 'datazone', 'DataZone', 'Name'),
    'W': Geography(WestminsterConstituency, 'code', 'CODE', 'NAME'),
    'L': Geography(LocalAuthority, 'code', 'code', 'local_auth')}


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--init-db', default=False, action='store_true',
                       help="initialise tables")
    group.add_argument('--delete-db', default=False, action='store_true',
                       help="drop tables")
    group.add_argument('-g', '--geography', choices=GEOGRAPHIES.keys(),
                       help='the geography type (D) datazone, (W) Westminster '
                       'Constituency, (L) local authority')
    group.add_argument('-y', '--year', type=int, choices=MAPPING.keys(),
                       help="load data for YEAR")
    group.add_argument('-a', '--attributes', type=Path,
                       help="read configuration file describing attributes")
    parser.add_argument('data', type=Path, nargs='?',
                        help="the data file to load")
    args = parser.parse_args()

    app = init_app()

    if args.init_db:
        with app.app_context():
            db.create_all()
    elif args.delete_db:
        with app.app_context():
            db.drop_all()
    elif args.geography is not None:
        if args.data is None:
            parser.error('no shape file specified')
        with app.app_context():
            geography = GEOGRAPHIES[args.geography]
            with fiona.open(args.data, 'r') as geography_data:
                # setup projection
                shp_projection = pyproj.CRS(geography_data.crs_wkt)
                project = pyproj.Transformer.from_crs(
                    shp_projection, DB_PROJECTION, always_xy=True).transform
                for geo in geography_data:
                    if not geo['properties'][geography.id][0] == 'S':
                        # only load Scottish data
                        continue
                    poly = transform(project, shape(geo['geometry']))
                    data = {geography.dbid: geo['properties'][geography.id],
                            'name': geo['properties'][geography.name],
                            'geometry': poly.wkt}
                    data = geography.cls(**data)
                    db.session.add(data)
            db.session.commit()
    elif args.year is not None:
        if args.data is None:
            parser.error('no CSV specified')

        with app.app_context():
            # first load data
            mapping = MAPPING[args.year]
            data = pandas.read_csv(args.data)
            to_drop = [k for k in data.keys() if k not in mapping]
            data.drop(to_drop, axis=1, inplace=True)
            data.rename(columns=mapping, inplace=True)
            data['year'] = args.year
            for record in data.to_dict(orient='records'):
                record = Data(**record)
                db.session.add(record)
            db.session.commit()

            # aggregate data for other geographies
            for GeoTable, DataTable in [
                    (WestminsterConstituency, DataWestminster),
                    (LocalAuthority, DataLocalAuthority)]:
                zones = db.session.query(GeoTable)
                for zone in zones:
                    datazones = db.session.query(DataZone.datazone).filter(
                        DataZone.geometry.ST_Within(zone.geometry)).subquery()
                    data = db.session.query(
                        db.func.sum(
                            Data.total_population).label('total_population'),
                        db.func.sum(Data.alcohol).label('alcohol'),
                        db.func.sum(Data.drug).label('drug')).filter(
                        Data.datazone_id.in_(datazones)).one()
                    zoneData = DataTable(code_id=zone.code, **data._asdict())
                    db.session.add(zoneData)
                db.session.commit()
    elif args.attributes is not None:
        cfg = configparser.ConfigParser()
        cfg.read(args.attributes)
        for a in cfg.keys():
            if a in ['setup', 'DEFAULT']:
                continue
            if not hasattr(Data, a):
                print(f'Error, unknown attribute {a}')
                sys.exit(1)
            if 'name' not in cfg[a]:
                name = a
            else:
                name = cfg[a]['name']
            dfile = (args.attributes.parent / 'descriptions' / a).with_suffix(
                '.md')
            if dfile.exists():
                with dfile.open('r') as dfile:
                    description = markdown.markdown(dfile.read())
            else:
                description = ''

            with app.app_context():
                db.session.merge(
                    Attribute(attribute=a, name=name, description=description))
                db.session.commit()


if __name__ == '__main__':
    main()
