from app import db
from app.models import Instrument,Metric

class Sensor(db.Model):
    __tablename__ = 'sensors'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode)
    instrument_id = db.Column(db.Integer, db.ForeignKey('instruments.id'))
    metric_id = db.Column(db.Integer, db.ForeignKey('variables.id'))
    
    metric = db.relationship('Metric')
    instrument = db.relationship('Instrument')

    def __init__(self,name):
        self.name = name
