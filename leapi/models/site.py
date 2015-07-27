from leapi import db

class Site(db.Model):
    __tablename__ = 'sites'

    id = db.Column(db.Unicode, primary_key=True)
    name = db.Column(db.Unicode, unique=True)
    description = db.Column(db.Unicode)
    instruments = db.relationship('Instrument', backref='site', lazy='dynamic')
    observations = db.relationship('Observation', backref='site', lazy="dynamic")
    location_id = db.Column(db.ForeignKey('locations.id'))

    location = db.relationship('Location')

    def __repr__(self):
        return "{}: {}".format(self.id, self.name)
