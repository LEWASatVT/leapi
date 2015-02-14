import sys

sys.path.append('./')
sys.path.append('../')

from app import db, models

variables = [ ('flow','water'),
              ('velocity','water'),
              ('temperature','water'),
              ('temperature','air'),
              ('dissolved oxygen','water'),
              ('pressure','air'),
              ('conductivity','water'),
              ('current','battery'),
              ('voltage','battery')]


units = [('degrees celsius', 'C', 'temperature'),
         ('meters per second', 'm/s', 'distance/time'),
         ('miligrams per liter', 'mg/L', 'mass/volume'),
         ('inches of mercury','in', 'pressure'),
         ('percent humidity', '%', 'percentage')]

instruments = [ ('weather station', 'stroubles1'),
                ('sonde', 'stroubles1'),
                ('argonaut', 'stroubles1')]

sensors = [ ('temperature', 'weather station', ('temperature', 'air')),
            ('velocity', 'argonaut', ('velocity', 'water')),
            ('temperature', 'sonde', ('temperature', 'water'))]

cinstruments = [ (i.name,i.site_id) for i in models.Instrument.query.all() ]
cvariables = [ (v.name,v.medium) for v in models.Variable.query.all() ]
cunits = [ (u.name, u.abbv, u.type) for u in models.Unit.query.all() ]
csensors = [ (s.name, s.instrument) for s in models.Sensor.query.all() ]

for (name,site_id) in instruments:
    if (name,site_id) not in cinstruments:
        site = models.Site.query.get(site_id)
        i = models.Instrument(name=unicode(name))
        i.site = site
        db.session.add(i)

for (name,medium) in variables:
    if (name,medium) not in cvariables:
        v = models.Variable(name=unicode(name), medium=unicode(medium))
        db.session.add(v)

for (name,abbv,utype) in units:
    if (name,abbv,utype) not in cunits:
        u = models.Unit(name=unicode(name), abbv=unicode(abbv), type=unicode(utype))
        db.session.add(u)

for (name, instrument, (vname, vmedium)) in sensors:
    if (name,instrument) not in csensors:
        s = models.Sensor(name)
        s.instrument = models.Instrument.query.filter_by(name=instrument).first()
        s.variable = models.Variable.query.filter_by(name=vname, medium=vmedium).first()
        db.session.add(s)

db.session.commit()
