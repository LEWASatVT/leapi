from app import db

class Site(db.Model):
    __tablename__ = 'sites'

    id = db.Column(db.Unicode, primary_key=True)
    name = db.Column(db.Unicode, unique=True)
    description = db.Column(db.Unicode)
    instruments = db.relationship('Instrument', backref='site', lazy='dynamic')

