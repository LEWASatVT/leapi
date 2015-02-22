#!/usr/bin/env python

import datetime
import random
import json

obs = dict(value=42.42, 
           datetime=str(datetime.datetime.now()), 
           units=dict(abbv='mS/cm'), 
           metric=dict(name='specific conductance', medium='water')
)

print(json.dumps(obs))
