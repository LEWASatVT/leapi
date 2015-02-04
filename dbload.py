#!/bin/env python
from app import app,db,models

import MySQLdb

def insert_sql(record):
    return """(TIMESTAMP '{dt}', {temp}, (SELECT id FROM sensors WHERE name='temperature')),
    (TIMESTAMP '{dt}', {humidity}, (SELECT id FROM sensors WHERE name='humidity')),
    (TIMESTAMP '{dt}', {pressure}, (SELECT id FROM sensors WHERE name='pressure'))
    """.format(dt=record[1], temp=record[2], humidity=record[3], pressure=record[4])
mdb = MySQLdb.connect("localhost", "root", "", "lewas_legacy")
cursor = mdb.cursor()

cursor.execute("SELECT * FROM PTH")

def load_or_create(model, vname):
    vmodel = model.query.filter_by(name=vname).first()
    if not vmodel:
        vmodel = model(name=vname)
        db.session.add(vmodel)
    return vmodel

def ensure(model, variables):
    variables = dict([ (vname, load_or_create(model, vname)) for vname in variables ])
    db.session.commit()
    return variables

variables = ensure(models.Variable, [ 'temperature', 'humidity', 'pressure' ])
units = ensure(models.Unit, [ 'Celsius', 'relative humidity', 'atmospheric pressure' ])

def dictify(keys, mytuple):
    return dict(zip(keys,mytuple))

def add_observations(record,units,variables):
    obst = models.Observation(value=record[2],datetime=record[1],units=units['Celsius'], variable=variables['temperature'])
    obsh = models.Observation(value=record[3],datetime=record[1],units=units['relative humidity'], variable=variables['humidity'])
    obsp = models.Observation(value=record[4],datetime=record[1],units=units['atmospheric pressure'], variable=variables['pressure'])
    return (obst,obsh,obsp)

records = cursor.fetchall()
import itertools

obs = [ a for a in itertools.chain(*[ add_observations(r,units,variables) for r in records ]) ]

for mslice in ( obs[i:i+100] for i in range(0, len(obs), 100) ):
    [ db.session.add(t) for t in mslice ]
    db.session.commit()
