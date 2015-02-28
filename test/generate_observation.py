#!/usr/bin/env python

import datetime
import random
import json

obs = dict(value=42.42, 
           std_error=0.01,
           datetime=str(datetime.datetime.now()), 
           units=dict(abbv='mS/cm'), 
           metric=dict(name='specific conductance', medium='water'),
           offset_value=0.42,
           offset_type=dict(id=1)
)

print(json.dumps(obs))
