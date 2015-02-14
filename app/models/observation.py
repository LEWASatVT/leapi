from app import db
from app import hal
from sqlalchemy import UniqueConstraint

class Observation(db.Model):
    __tablename__ = 'observations'
    __metaclass__ = hal.MetaHal
    __table_args__ = (UniqueConstraint('site_id','sensor_id','datetime',name='key_1'),)

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Float)
    datetime = db.Column(db.DateTime)
    site_id = db.Column(db.String, db.ForeignKey('sites.id'))
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensors.id'))
    variable_id = db.Column(db.Integer, db.ForeignKey('variables.id'))
    variable = db.relationship('Metric')
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'))
    units = db.relationship('Unit')

    def __repr__(self):
        return "{0}: {1} {2}".format(self.datetime, self.value, self.units)

    #@link
    #def self(self):
    #    return "/observation/{}".format(self.id)

    #@link
    #def timeseries(self):
    #    return "/timeseries/{}".format(self.variable_id)

    def links(self):
        return [ {'timeseries': { 'href': '/timeseries/' }} ]

    def curies(self):
        return [{ 'name': 'le', 'href': 'http://example.com/docs/rels/{rel}', 'templated': True }]
