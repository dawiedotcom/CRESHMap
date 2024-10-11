"""Data models."""
from . import db
from geoalchemy2 import Geometry


URBAN_RURAL_CLASSIFICATION = ['UR2', 'UR3', 'UR6', 'UR8']


class Lookup(db.Model):
    __tablename__ = 'lookup'

    dz = db.Column(db.String(10), primary_key=True)
    iz = db.Column(db.String(10))
    mmward = db.Column(db.String(10))
    la = db.Column(db.String(10))
    spc = db.Column(db.String(10))
    ukpc = db.Column(db.String(10))
    hb = db.Column(db.String(10))
    hia = db.Column(db.String(10))
    spd = db.Column(db.String(10))
    sfrlso = db.Column(db.String(10))
    sfrsda = db.Column(db.String(10))
    rrp = db.Column(db.String(10))
    lrp = db.Column(db.String(10))
    ttwa = db.Column(db.String(10))
    ur2 = db.Column(db.Integer)
    ur3 = db.Column(db.Integer)
    ur6 = db.Column(db.Integer)
    ur8 = db.Column(db.Integer)


class GeographyTypes(db.Model):
    __tablename__ = 'cresh_geography_types'

    gss_code = db.Column(db.String(3), primary_key=True)
    name = db.Column(db.String())
    column_name = db.Column(db.String())

    geographies = db.relationship('Geography', backref='type')


class Geography(db.Model):
    __tablename__ = 'cresh_geography'

    gss_id = db.Column(db.String(10), primary_key=True)
    gss_code = db.Column(
        db.String(3), db.ForeignKey('cresh_geography_types.gss_code'))
    name = db.Column(db.String())
    geometry = db.Column(Geometry('GEOMETRY', srid=4326))


class Variables(db.Model):
    __tablename__ = 'variables'

    id = db.Column(db.String(), primary_key=True)
    variable = db.Column(db.String(), unique=True)
    domain = db.Column(db.String())
    description = db.Column(db.String())


class Data(db.Model):
    __tablename__ = 'data'

    id = db.Column(db.Integer, primary_key=True)
    variable_id = db.Column(db.String(), db.ForeignKey('variables.id'))
    gss_id = db.Column(db.String(10), db.ForeignKey('cresh_geography.gss_id'))
    year = db.Column(db.Integer)
    value = db.Column(db.Float)
    color = db.Column(db.String(10))

    __table_args__ = (
        db.UniqueConstraint(
            "variable_id", "gss_id", "year", name='_unique_data'), )

class TextQuotes(db.Model):
    __tablename__ = 'cresh_text_quotes'
    id = db.Column(db.Integer, primary_key=True)
    # NOTE: ST_Centroid is slow on stream/pow so the geometry is cached when reading data
    dz_name = db.Column(db.String())
    geometry = db.Column(Geometry(geometry_type='POINT', srid=4326))
    gss_id = db.Column(db.String(10), db.ForeignKey('cresh_geography.gss_id'), index=True)
    value = db.Column(db.String())


class Images(db.Model):
    __tablename__ = 'cresh_images'
    id = db.Column(db.Integer, primary_key=True)
    dz_name = db.Column(db.String())
    geometry = db.Column(Geometry(geometry_type='POINT', srid=4326))
    gss_id = db.Column(db.String(10), db.ForeignKey('cresh_geography.gss_id'), index=True)
    filename = db.Column(db.String())

class DownloadLink(db.Model):
    __tablename__ = 'download_link'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String())
    download_hash = db.Column(db.String())
    salt = db.Column(db.String())
    last_accessed = db.Column(db.DateTime())
    organization = db.Column(db.String())
    name = db.Column(db.String())
