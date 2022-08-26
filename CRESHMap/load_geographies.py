from . import init_app, db
from .models import URBAN_RURAL_CLASSIFICATION
from .models import Lookup
from .models import GeographyTypes
from .models import Geography

import argparse
from pathlib import Path
import requests
import shutil
import yaml
from yaml.loader import SafeLoader
import pandas
import zipfile
import fiona
from shapely.geometry import shape
from shapely.ops import transform
import pyproj
from sqlalchemy import update


def download_file(url, destination):
    """download url and save to file

    from stackoverflow: https://stackoverflow.com/a/39217788"""
    if destination.exists():
        return

    with requests.get(url, stream=True) as r:
        with destination.open('wb') as f:
            shutil.copyfileobj(r.raw, f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=Path, help="name of configuration file")
    args = parser.parse_args()

    app = init_app()

    # read configuration
    with open(args.config) as f:
        cfg = yaml.load(f, Loader=SafeLoader)

    data_files = {}
    for data in cfg['data']:
        data_files[data['name']] = data

    tmp_dir = Path(cfg['tmp_directory'])

    with app.app_context():
        # always recreate tables
        db.drop_all()
        db.create_all()

        # download data
        download = tmp_dir / 'downloads'
        download.mkdir(parents=True, exist_ok=True)
        for data in cfg['data']:
            download_file(data['download'], download / data['file'])

        lookup_mapping = {}
        for data in cfg['geography_types']:
            gt = GeographyTypes(column_name=data['db_name'],
                                gss_code=data['code'], name=data['name'])
            db.session.add(gt)
            if 'col_name' in data:
                lookup_mapping[data['col_name']] = data['db_name']
        db.session.commit()

        # read lookup table
        lookup = pandas.read_csv(
            download / data_files['datazone lookup']['file'],
            encoding=data_files['datazone lookup']['encoding'])

        for col_name in lookup_mapping:
            code = f'{col_name}_Code'
            name = f'{col_name}_Name'
            geographies = lookup[
                [code, name]].drop_duplicates()
            for g in geographies.itertuples():
                geography = Geography(
                    gss_code=getattr(g, code)[:3],
                    gss_id=getattr(g, code), name=getattr(g, name))
                db.session.add(geography)
            db.session.commit()

        for u in URBAN_RURAL_CLASSIFICATION:
            lookup_mapping[u] = u.lower()
        for l in lookup.itertuples():
            data = {}
            for g in lookup_mapping:
                data[lookup_mapping[g]] = getattr(l, f"{g}_Code")
            lookup_entry = Lookup(**data)
            db.session.add(lookup_entry)
        db.session.commit()

        # extract and load datazone boundaries
        zipname = download / data_files['datazone boundaries']['file']
        shpname = zipname.with_suffix('.shp')
        if not shpname.exists():
            with zipfile.ZipFile(zipname, 'r') as zip_bndries:
                zip_bndries.extractall(download)
        with fiona.open(shpname, 'r') as boundaries:
            # setup projection
            shp_projection = pyproj.CRS(boundaries.crs_wkt)
            project = pyproj.Transformer.from_crs(
                shp_projection, pyproj.CRS(cfg['projection']),
                always_xy=True).transform

            for geo in boundaries:
                if not geo['properties']['DataZone'][0] == 'S':
                    # only load Scottish data
                    continue
                poly = transform(project, shape(geo['geometry']))
                db.session.query(Geography).filter(
                    Geography.gss_id == geo['properties']['DataZone']).\
                    update({'geometry': poly.wkt})
            db.session.commit()

        # compute boundaries for remaining zones
        for geotype in db.session.query(GeographyTypes).all():
            if geotype.gss_code in ['S01', 'K01']:
                # nothing to be done for data zones
                continue
            print(geotype.gss_code, geotype.column_name)
            id_col = getattr(Lookup, geotype.column_name)

            for gss_id, bdry in db.session.query(
                    id_col,
                    Geography.geometry.ST_Union().label('geometry')).\
                    join(Lookup, Lookup.dz == Geography.gss_id).\
                    group_by(id_col).all():
                db.session.execute(update(Geography).
                                   where(Geography.gss_id == gss_id).
                                   values(geometry=bdry))
            db.session.commit()


if __name__ == '__main__':
    main()
