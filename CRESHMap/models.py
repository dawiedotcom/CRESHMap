"""Data models."""
from . import db
from geoalchemy2 import Geometry
from sqlalchemy.orm.collections import attribute_mapped_collection


class DataZone(db.Model):
    __tablename__ = 'datazone'

    datazone = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String())
    geometry = db.Column(Geometry('GEOMETRY'))

    data = db.relationship(
        "Data",
        collection_class=attribute_mapped_collection("year"))


class Data(db.Model):
    __tablename__ = 'data'

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer)
    total_population = db.Column(db.Integer)
    working_age_population = db.Column(db.Integer)
    alcohol = db.Column(db.Float)
    drug = db.Column(db.Float)
    rank = db.Column(db.Integer)
    percentile = db.Column(db.Integer)
    income_domain_rank = db.Column(db.Integer)
    employment_domain_rank = db.Column(db.Integer)
    health_domain_rank = db.Column(db.Integer)
    education_domain_rank = db.Column(db.Integer)
    access_domain_rank = db.Column(db.Integer)
    crime_domain_rank = db.Column(db.Integer)
    housing_domain_rank = db.Column(db.Integer)

    datazone_id = db.Column(db.String(10), db.ForeignKey('datazone.datazone'))
    datazone = db.relationship("DataZone", back_populates="data")

    __table_args__ = (
        db.UniqueConstraint('year', 'datazone_id', name='_unique_params'), )
