import sys

sys.path.append('../')

from app import db, models

variables = [ ('flow','water'),
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

instruments = [ ('weather station'
cvariables = [ (v.name,v.medium) for v in models.Variable.query.all() ]
cunits = [ (u.name, u.abbv, u.type) for u in modes.Units.query.all() ]

for (name,medium) in variables:
    if (name,medium) not in cvariables:
        v = models.Variable(name=unicode(name), medium=unicode(medium))
        db.session.add(v)

for (name,abbv,utype) for units:
    if (name,abbv,utype) not in cunits:
        u = models.Unit(name=unicode(name), abbv=unicode(abbv), type=unicode(utype))
        db.session.add(u)

db.session.commit()
