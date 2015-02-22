#!/usr/bin/env python

import datetime
import random
import json

obs = dict(site=dict(id='test1'),
           value=42.42, 
           datetime=str(datetime.datetime.now()), 
           units=dict(abbv='mS/cm'), 
           metric=dict(name='specific conductance', medium='water'),
           sensor=dict(name='specific conductance',instrument_id=5),
           instrument=dict(id=5,name="sonde")
)

print(json.dumps(obs))
