from app import db
from app import hal
from sqlalchemy.dialects.postgresql import JSON

# huh, one of these days, check out MongoDB and evaluate for this application. It would make a good blog post ;-)
# http://blog.mongolab.com/2012/08/why-is-mongodb-wildly-popular/

class Site(db.Model):
    __tablename__ = 'sites'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode, unique=True)
    instruments = db.relationship('Instrument', backref='site', lazy='dynamic')

class Instrument(db.Model):
    __tablename__ = 'instruments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode, unique=True)
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id'))


    sensors = db.relationship('Sensor')

    def __init__(self,name):
        self.name = name

    def __repr__(self):
        return '<id {}>'.format(self.id)
        
class Sensor(db.Model):
    __tablename__ = 'sensors'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode)
    instrument_id = db.Column(db.Integer, db.ForeignKey('instruments.id'))

    def __init__(self,name):
        self.name = name

class Variable(db.Model):
    __tablename__ = 'variables'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode)
    medium = db.Column(db.Unicode)
    
    def __repr__(self):
        return "variable {}".format(self.name)

    @property
    def json(self):
        return dict(id=self.id, name=self.name, medium=self.medium)

class Unit(db.Model):
    __tablename__ = 'units'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode)
    abbv = db.Column(db.Unicode, unique=True)
    type = db.Column(db.Unicode)
    
    def __repr__(self):
        return "{0} ({1})".format(self.name, self.abbv)

    @property
    def json(self):
        return dict(id=self.id, name=self.name, abbv=self.abbv, type=self.type)
        
class Observation(db.Model):
    __tablename__ = 'observations'
    __metaclass__ = hal.MetaHal
    link = hal.makeLink()

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Float)
    datetime = db.Column(db.DateTime)
    variable_id = db.Column(db.Integer, db.ForeignKey('variables.id'))
    variable = db.relationship('Variable')
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

    @property
    def json(self):
        return dict(id=self.id, value=self.value, datetime=str(self.datetime), _embedded=dict(variable=self.variable.json, units=self.units.json))
