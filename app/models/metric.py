from app import db
from sqlalchemy import UniqueConstraint

class Metric(db.Model):
    __tablename__ = 'variables'
    __table_args__ = (UniqueConstraint('name','medium',name='uix_key'),)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode)
    medium = db.Column(db.Unicode)
    
    sensors = db.relationship('Sensor', backref='variable')

    def __repr__(self):
        return "{}: {} {}".format(self.id, self.medium, self.name)

    @property
    def json(self):
        return dict(id=self.id, name=self.name, medium=self.medium)

class CountedMetric(db.Model):
    __tablename__ = 'counted_metrics'

    count = db.Column(db.Integer)
    site_id = db.Column(db.Unicode)
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode)
    medium = db.Column(db.Unicode)
