from flask import Response
import itertools
from leapi import app
from leapi.models import Observation, Site, Instrument, Unit, Metric
from leapi.dateparser import DateParser
from datetime import datetime
from sqlalchemy import or_,and_
from collections import defaultdict, OrderedDict

test_metrics = [ ('rain','intensity'),
                 ('water','downstream velocity')
             ]
##TODO print header row
@app.route('/sites/<string:site_id>/archive.csv')
def generate_archive(site_id):
    dateparser = DateParser()
    metric_id=4
    filterexp = [Site.id==site_id,Observation.site_id==Site.id, Observation.instrument_id==Instrument.id, Observation.offset_value == None]
    yesterday = dateparser.parse('1 hour')
    filterexp.append(Observation.datetime>=yesterday)
    ors = []
    for m in test_metrics:
        ors.append(and_(Metric.medium==m[0], Metric.name==m[1]))
    
    filterexp.append(or_(*ors))
    def generate():
        q = Observation.query.join(Observation.metric,Site,Instrument).filter(*filterexp).order_by(Observation.datetime.desc()).group_by(Observation.datetime,Observation.id).all()

        for g,k in itertools.groupby(q, lambda a: datetime(a.datetime.year,a.datetime.month,a.datetime.day,a.datetime.hour,a.datetime.minute)):
            row = list(k)
            row = dict([ ("{} {}".format(o.metric.medium, o.metric.name), o.value) for o in row ])
            yield ','.join([str(g)] + [ str(v) for v in row.values()]) + '\n'

    return Response(generate(), mimetype='text/csv')
