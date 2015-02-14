from app import db

class Sensor(db.Model):
    __tablename__ = 'sensors'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode)
    instrument_id = db.Column(db.Integer, db.ForeignKey('instruments.id'))
    variable_id = db.Column(db.Integer, db.ForeignKey('variables.id'))

    def __init__(self,name):
        self.name = name
