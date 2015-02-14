from app import db

class Instrument(db.Model):
    __tablename__ = 'instruments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode, unique=True)
    model = db.Column(db.Unicode)
    manufacturer = db.Column(db.Unicode)
    site_id = db.Column(db.Unicode, db.ForeignKey('sites.id'))

    sensors = db.relationship('Sensor', backref='instrument')

    def __init__(self,name):
        self.name = name

    def __repr__(self):
        return '<id {}>'.format(self.id)
