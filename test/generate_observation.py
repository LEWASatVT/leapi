#!/usr/bin/env python

import datetime
import random
obs = dict(value=random.randint(1,10), datetime=str(datetime.datetime.now()), unit_id=dict(id='1'), variable_id=dict(id='1'))

print(obs)
