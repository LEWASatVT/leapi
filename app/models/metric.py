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
        return "variable {}".format(self.name)

    @property
    def json(self):
        return dict(id=self.id, name=self.name, medium=self.medium)
