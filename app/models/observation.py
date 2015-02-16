from app import db
from app import hal
from sqlalchemy import UniqueConstraint

class Observation(db.Model):
    __tablename__ = 'observations'
    #__metaclass__ = hal.MetaHal
    __table_args__ = (UniqueConstraint('site_id','instrument_id','metric_id', 'datetime',name='key_1'),)

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Float)
    datetime = db.Column(db.DateTime)
    site_id = db.Column(db.String, db.ForeignKey('sites.id'), nullable=False)
    instrument_id = db.Column(db.Integer, db.ForeignKey('instruments.id'), nullable=False)
    metric_id = db.Column(db.Integer, db.ForeignKey('variables.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)

    metric = db.relationship('Metric')
    units = db.relationship('Unit')
    instrument = db.relationship('Instrument')
