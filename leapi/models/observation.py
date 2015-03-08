from leapi import db
from leapi import hal
from sqlalchemy import UniqueConstraint

class OffsetType(db.Model):
    __tablename__ = 'offsettypes'

    id = db.Column(db.Integer, primary_key=True)
    units_id = db.Column(db.Integer, db.ForeignKey('units.id'))
    description = db.Column(db.Unicode)

    units = db.relationship('Unit')

class Observation(db.Model):
    __tablename__ = 'observations'
    #__metaclass__ = hal.MetaHal
    __table_args__ = (UniqueConstraint('site_id','instrument_id','metric_id', 'datetime',name='key_1'),)

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Float)
    stderr = db.Column(db.Float)
    datetime = db.Column(db.DateTime)
    site_id = db.Column(db.String, db.ForeignKey('sites.id'), nullable=False)
    instrument_id = db.Column(db.Integer, db.ForeignKey('instruments.id'), nullable=False)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensors.id') ) #TODO once established, make nullable=False
    metric_id = db.Column(db.Integer, db.ForeignKey('variables.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    offset_value = db.Column(db.Float)
    offset_type_id = db.Column(db.Integer, db.ForeignKey('offsettypes.id') )

    metric = db.relationship('Metric')
    units = db.relationship('Unit')
    instrument = db.relationship('Instrument')
    sensor = db.relationship('Sensor')
    offset_type = db.relationship('OffsetType')
