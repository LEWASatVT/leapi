from leapi import db
from leapi.models import Instrument,Metric
from sqlalchemy import ForeignKeyConstraint

class Sensor(db.Model):
    __tablename__ = 'sensors'
    __table_args__ = (ForeignKeyConstraint(['site_id','instrument_name'], ['instruments.site_id','instruments.name']),)
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode)
    site_id = db.Column(db.Unicode, db.ForeignKey('sites.id'))
    instrument_name = db.Column(db.Unicode)
    metric_id = db.Column(db.Integer, db.ForeignKey('variables.id'))
    
    metric = db.relationship('Metric')
    instrument = db.relationship('Instrument')

    def __init__(self,name):
        self.name = name
