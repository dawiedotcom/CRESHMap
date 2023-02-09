from . import init_app, db
from .models import TextQuotes
from .models import Images
from .models import Geography

import argparse
from pathlib import Path
import pandas
#import yaml
import zipfile
from xml.dom import minidom
from pathlib import Path
import os
import shutil
import uuid
from sqlalchemy.sql.expression import func

def import_text(data):
    # Load text columns
    data_zone_id = data.columns[0]
    text_data = pandas.DataFrame(columns=['dz_name', 'geometry', 'gss_id', 'value'])
    for column in data.columns[1:]:
        idx = data.loc[:, column] == data.loc[:, column]
        new_data = data.loc[idx, [data_zone_id, column]]
        new_data = new_data.rename(columns={
            data_zone_id: 'gss_id',
            column: 'value'
        })
        names_geoms = db.session.query(
            Geography.name,
            func.ST_AsText(func.ST_Centroid(Geography.geometry))
        ).where(
            Geography.gss_id.in_(new_data['gss_id'])
        ).all()
        new_data['dz_name'] = [ng[0] for ng in names_geoms]
        new_data['geometry'] = [ng[1] for ng in names_geoms]

        text_data = pandas.concat((text_data, new_data))

    text_data.to_sql(
        'cresh_text_quotes',
        con=db.session.get_bind(),
        index=False,
        if_exists='append',
        method='multi',
    )


def import_images(filename, data):
    tmp_dir = filename.parent / filename.stem
    with zipfile.ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall( str(tmp_dir) )

    images = {}
    # Could there be more than one drawing*.xml?
    drawing_dir = tmp_dir / Path('xl/drawings')
    for xml_filename in drawing_dir.glob('drawing*.xml'):
        xml = minidom.parse(str(xml_filename))
        for anchor in xml.getElementsByTagName('xdr:twoCellAnchor'):
            blip = anchor.getElementsByTagName('a:blip')[0]
            image_id = blip.attributes['r:embed'].value
            images[image_id] = {}
            row = int(anchor.getElementsByTagName('xdr:row')[0].firstChild.data)-1
            images[image_id]['row'] = row
            datazone = data.loc[row, data.columns[0]]
            images[image_id]['datazone'] = datazone

    rel_dir = tmp_dir / Path('xl/drawings/_rels/') #*.xml.rels')
    for rel in rel_dir.glob('*.xml.rels'):
        xml = minidom.parse(str(rel))
        for r in xml.getElementsByTagName('Relationship'):
            image_id = r.attributes['Id'].value
            image_dir = r.attributes['Target'].value
            images[image_id]['path'] = tmp_dir / Path('xl/media') / Path(image_dir).parts[-1]

    sql_data = []
    for image in images.values():
        f = open(str(image['path']))
        with open(str(image['path']), 'rb') as f:
            content = f.read()
            new_name = uuid.uuid3(uuid.NAMESPACE_URL, str(content))
        new_name = str(new_name) + image['path'].suffix

        local_dir = Path('CRESHMap') # This script needs to keep track of this extra director, but the js client does not. So CRESHMap/ does not go in the database, but needs to be included in the copy operation.
        image_dir = Path('static/images/qual')
        new_name =  image_dir / Path(new_name)

        dz_name, geometry = db.session.query(
            Geography.name,
            func.ST_AsText(func.ST_Centroid(Geography.geometry))
        ).where(
            Geography.gss_id == image["datazone"]
        ).one()

        sql_data.append(Images(
            dz_name=dz_name,
            geometry=geometry,
            gss_id=image['datazone'],
            filename=str(new_name),
        ))

        if not os.path.exists(str(local_dir / image_dir)):
            os.mkdir(str(local_dir / image_dir))
        if not os.path.exists(str(local_dir / new_name)):
            shutil.copy(
                str(image['path']),
                str(local_dir / new_name)
            )

    db.session.add_all(sql_data)
    db.session.commit()

def main():
    parser = argparse.ArgumentParser("Load qualitative data into the database")
    parser.add_argument('datafile', type=Path, help="Name of an Excel file mapping Data Zones to text or images")
    args = parser.parse_args()

    app = init_app()

    data = pandas.read_excel(args.datafile)

    with app.app_context():
        # Make sure all the table exist
        db.create_all()

        import_text(data)
        import_images(args.datafile, data)


