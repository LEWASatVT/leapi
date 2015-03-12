from leapi import db
from leapi import hal
from sqlalchemy import UniqueConstraint, ForeignKeyConstraint

class OffsetType(db.Model):
    __tablename__ = 'offsettypes'

    id = db.Column(db.Integer, primary_key=True)
    units_id = db.Column(db.Integer, db.ForeignKey('units.id'))
    description = db.Column(db.Unicode)

    units = db.relationship('Unit')

class Observation(db.Model):
    __tablename__ = 'observations'
    __table_args__ = (UniqueConstraint('site_id','instrument_name','metric_id', 'datetime',name='key_1'),
                      ForeignKeyConstraint(['site_id','instrument_name'], ['instruments.site_id','instruments.name'],name='observation_instrument_fk'),)

    #After adding instrument_name column:
    #UPDATE observations AS o SET instrument_name = i.name FROM instruments AS i WHERE o.instrument_id = i.id WHERE o.instrument_name IS NULL;
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Float)
    stderr = db.Column(db.Float)
    datetime = db.Column(db.DateTime)
    site_id = db.Column(db.String, db.ForeignKey('sites.id'), nullable=False)
    instrument_name = db.Column(db.String)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensors.id') ) #TODO once established, make nullable=False
    metric_id = db.Column(db.Integer, db.ForeignKey('variables.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    offset_value = db.Column(db.Float)
    offset_type_id = db.Column(db.Integer, db.ForeignKey('offsettypes.id') )

    metric = db.relationship('Metric')
    units = db.relationship('Unit')
    instrument = db.relationship('Instrument', foreign_keys=[site_id,instrument_name]) 
    sensor = db.relationship('Sensor')
    offset_type = db.relationship('OffsetType')

    @property
    def offset(self):
        return {'value': self.offset_value, 'type_id': self.offset_type_id, 'type': self.offset_type.description } 
