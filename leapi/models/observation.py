from leapi import db
from leapi import hal
from sqlalchemy import UniqueConstraint, ForeignKeyConstraint

derived_from_table = db.Table('derived_from', db.metadata,
                        #TODO: add constraint derived_from_id must be different from observation_id      
                        db.Column('derived_from_id', db.Integer, db.ForeignKey('observations.id'), primary_key=True),
                        db.Column('observation_id', db.Integer, db.ForeignKey('observations.id'), primary_key=True)
              )

flags_relation_table = db.Table('observation_flags', db.metadata,
                                db.Column('observation_id', db.ForeignKey('observations.id')),
                                db.Column('flag_id', db.ForeignKey('flags.id'))
)

class OffsetType(db.Model):
    __tablename__ = 'offsettypes'

    id = db.Column(db.Integer, primary_key=True)
    units_id = db.Column(db.Integer, db.ForeignKey('units.id'))
    description = db.Column(db.Unicode)

    units = db.relationship('Unit')

class Observation(db.Model):
    __tablename__ = 'observations'
    __table_args__ = (UniqueConstraint('site_id','instrument_name','metric_id',
                                       'datetime', 'value', 'offset_value',
                                       'offset_type_id','method_id',
                                       name='unique_observation'),
                      ForeignKeyConstraint(['site_id','instrument_name'], ['instruments.site_id','instruments.name'],name='observation_instrument_fk'),)

    #After adding instrument_name column:
    #UPDATE observations AS o SET instrument_name = i.name FROM instruments AS i WHERE o.instrument_id = i.id WHERE o.instrument_name IS NULL;
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Float)
    stderr = db.Column(db.Float)
    datetime = db.Column(db.DateTime(timezone=True))
    site_id = db.Column(db.String, db.ForeignKey('sites.id'), nullable=False)
    instrument_name = db.Column(db.String)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensors.id') ) #TODO once established, make nullable=False
    metric_id = db.Column(db.Integer, db.ForeignKey('variables.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    offset_value = db.Column(db.Float, nullable=False)
    offset_type_id = db.Column(db.Integer, db.ForeignKey('offsettypes.id'), nullable=False )
    method_id = db.Column(db.Integer, db.ForeignKey('methods.id'), default=0)
                          
    method = db.relationship('Method')
    metric = db.relationship('Metric')
    units = db.relationship('Unit')
    instrument = db.relationship('Instrument', foreign_keys=[site_id,instrument_name]) 
    sensor = db.relationship('Sensor')
    offset_type = db.relationship('OffsetType')
    derived_from = db.relationship('Observation',
                                   secondary=derived_from_table,
                                   secondaryjoin=id==derived_from_table.c.derived_from_id,
                                   primaryjoin=id==derived_from_table.c.observation_id,
                                   backref="used_to_derive")
    flags = db.relationship('Flag',
                            secondary=flags_relation_table)

    @property
    def offset(self):
        return {'value': self.offset_value, 'type_id': self.offset_type_id, 'type': self.offset_type.description } 

    def __unicode__(self):
        value = u"{} {} of {}({})".format(self.metric.medium, self.metric.name, self.value, self.units.abbv)
        if self.stderr:
            value = value + u" \u03C3{}".format(self.stderr)
        if self.offset_type:
            value = value + u" offset {} {}".format(self.offset_type.description, self.offset_value)
        return value + u" observed by {} at {}".format(self.instrument.name, self.site.name).encode('utf-8')
        
    def __str__(self):
        return unicode(self).encode('utf-8')

    def __repr__(self):
        return "Observation {}: {}({}), {}".format(getattr(self,'id','unbound'),
                                                   self.value,
                                                   self.units.abbv,
                                                   {'instrument': self.instrument.name, 'site_id': self.site.id}).encode('utf-8')
