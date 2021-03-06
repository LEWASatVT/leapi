from leapi import db

class Unit(db.Model):
    __tablename__ = 'units'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode)
    abbv = db.Column(db.Unicode, unique=True)
    type = db.Column(db.Unicode)
    
    def __repr__(self):
        return "{0} ({1})".format(self.name, self.abbv)
