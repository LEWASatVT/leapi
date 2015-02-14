from app import db

class Metric(db.Model):
    __tablename__ = 'variables'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode)
    medium = db.Column(db.Unicode)
    
    sensors = db.relationship('Sensor', backref='variable')

    def __repr__(self):
        return "variable {}".format(self.name)

    @property
    def json(self):
        return dict(id=self.id, name=self.name, medium=self.medium)
