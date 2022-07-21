"""Data models."""
from . import db
from geoalchemy2 import Geometry
from sqlalchemy.orm.collections import attribute_mapped_collection
import math


class Geography(db.Model):
    __tablename__ = 'geography'

    geography = db.Column(db.String(), primary_key=True)
    name = db.Column(db.String())


class Attribute(db.Model):
    __tablename__ = 'attribute'

    attribute = db.Column(db.String(), primary_key=True)
    name = db.Column(db.String())
    description = db.Column(db.String())


class DataZone(db.Model):
    __tablename__ = 'datazone'

    datazone = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String())
    geometry = db.Column(Geometry('GEOMETRY'))

    data = db.relationship(
        "Data",
        collection_class=attribute_mapped_collection("year"))


class WestminsterConstituency(db.Model):
    __tablename__ = 'westminster_const'

    code = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String())
    geometry = db.Column(Geometry('GEOMETRY'))

    data = db.relationship(
        "DataWestminster",
        collection_class=attribute_mapped_collection("year"))


class LocalAuthority(db.Model):
    __tablename__ = 'local_authority'

    code = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String())
    geometry = db.Column(Geometry('GEOMETRY'))

    data = db.relationship(
        "DataLocalAuthority",
        collection_class=attribute_mapped_collection("year"))


class BaseData(db.Model):
    __tablename__ = 'base_data'

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer)
    total_population = db.Column(db.Integer)
    alcohol = db.Column(db.Float)
    drug = db.Column(db.Float)
    alcohol_density = db.Column(db.Float)
    drug_density = db.Column(db.Float)

    geography = db.Column(db.String)

    __mapper_args__ = {
        'polymorphic_identity': 'base_data',
        'polymorphic_on': geography}


def compute_densities(mapper, connection, target):
    if target.total_population == 0:
        target.alcohol_density = math.nan
        target.drug_density = math.nan
    else:
        target.alcohol_density = target.alcohol / target.total_population
        target.drug_density = target.drug / target.total_population


db.event.listen(BaseData, 'before_insert', compute_densities, propagate=True)


db.event.listen(BaseData, 'before_update', compute_densities, propagate=True)


class Data(BaseData):
    __tablename__ = 'data'

    id = db.Column(db.Integer,
                   db.ForeignKey('base_data.id', ondelete='CASCADE'),
                   primary_key=True)
    datazone_id = db.Column(db.String(10), db.ForeignKey('datazone.datazone'))
    datazone = db.relationship("DataZone", back_populates="data")

    __mapper_args__ = {
        'polymorphic_identity': 'datazone'}


class DataWestminster(BaseData):
    __tablename__ = 'data_westminster'

    id = db.Column(db.Integer,
                   db.ForeignKey('base_data.id', ondelete='CASCADE'),
                   primary_key=True)
    code_id = db.Column(db.String(10), db.ForeignKey('westminster_const.code'))
    constituency = db.relationship("WestminsterConstituency",
                                   back_populates="data")

    __mapper_args__ = {
        'polymorphic_identity': 'westminster_const'}


class DataLocalAuthority(BaseData):
    __tablename__ = 'data_local_authority'

    id = db.Column(db.Integer,
                   db.ForeignKey('base_data.id', ondelete='CASCADE'),
                   primary_key=True)
    code_id = db.Column(db.String(10), db.ForeignKey('local_authority.code'))
    local_authority = db.relationship("LocalAuthority",
                                      back_populates="data")

    __mapper_args__ = {
        'polymorphic_identity': 'local_authority'}
