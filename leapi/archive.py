from flask import Response
from flask.ext.restful import inputs
import itertools
from collections import defaultdict,OrderedDict

from leapi import app,api,db
from leapi.models import Observation, Site, Instrument, Unit, Metric
from leapi.dateparser import DateParser
from datetime import datetime
from sqlalchemy import or_,and_
from collections import defaultdict, OrderedDict
from sqlalchemy.sql import func
from sqlalchemy.orm import aliased

def inputList(typefn, delim=","):
    """parses a deliminated string into a list of items
    
    :param typefn: type function that will be applied to each string item
    :param delim: delimiter character, defaults to ','
    :return: a list of parsed values
    :rtype: A list [n1,n2,...]
    """
    def _make_list(values):
        print("making list from {}".format(values))
        return [ typefn(v) for v in values.split(',') ]
    
    return _make_list

import re
def decorated_id(typefn):
    class _decorated_id(object):
        def __init__(self, value, stderr=False):
            self.value = value
            self.stderr = stderr

        def __int__(self):
            return int(self.value)
            
        def __float__(self):
            return float(self.value)

        def __repr__(self):
            s = str(self.value) + '~' if self.stderr else ''
            return s

    def _input_parser(value):
        m = re.match(r'([0-9]+)(~?)', value)
        if m:
            return _decorated_id(typefn(m.group(1)), m.group(2)=='~')
        else:
            return _decorated_id(None)

    return _input_parser

parser = api.parser()
parser.add_argument('metrics', type=inputList(decorated_id(inputs.natural)), required=True, help="list of metric id's to include in archive", location='args')
parser.add_argument('interval', type=inputs.iso8601interval, required=True, help="iso8601 formated time interval", location='args')
parser.add_argument('instrument', type=str)
parser.add_argument('filename', type=str)

##TODO print header row
@app.route('/sites/<string:site_id>/archive.csv')
def generate_archive(site_id):
    args = parser.parse_args()
    metric_ids = [ int(mid) for mid in args['metrics'] ]
    filterexp = [Observation.site_id==site_id,Observation.offset_value == 0]
    filterexp.append(Observation.metric_id.in_(metric_ids))
    filterexp.append(Observation.datetime.between(*args['interval']))
    if args['instrument']:
        filterexp.append(Observation.instrument_name==args['instrument'])
    
    def generate():
        print("generating query for metrics {} between {} and {}".format(metric_ids, *args['interval']))
        #q = db.session.query(\
        #                     func.date_trunc('minute',Observation.datetime)\
        #).select_from(Observation).\
        #    filter(*filterexp).\
        #    order_by(Observation.datetime.desc())
        mq = Metric.query.filter(Metric.id.in_(metric_ids))
        metrics = dict([ (m.id, " ".join([m.medium,m.name])) for m in mq ])
        headers = OrderedDict()
        for id in args['metrics']:
            headers[int(id)] = metrics[int(id)]
            if id.stderr:
                headers[str(id)] = metrics[int(id)] + " stderr"
            
        q = Observation.query.filter(*filterexp).order_by(Observation.datetime)
        yield ",".join(['datetime'] + headers.values()) + "\n"

        ## SELECT o.datetime AS datetime,a.value,b.value FROM (SELECT datetime,value,metric_id FROM observations WHERE metric_id IN (6,14) AND datetime BETWEEN '2015-02-11' AND '2015-02-16') AS o LEFT JOIN (SELECT datetime,value,metric_id FROM observations WHERE metric_id=6) a ON a.datetime=o.datetime LEFT JOIN (SELECT datetime,value,metric_id FROM observations WHERE metric_id=14) b ON b.datetime=o.datetime GROUP BY o.datetime,a.value,b.value ORDER BY o.datetime;

        def float_or_nan(value=None):
            if value is not None:
                return float(value)
            else:
                return ''
        

        for g,k in itertools.groupby(q, lambda a: datetime(a.datetime.year,a.datetime.month,a.datetime.day,a.datetime.hour,a.datetime.minute)):
            row = defaultdict(float_or_nan)
            for o in k:
                try:
                    row[headers[o.metric_id]] = o.value
                    row[headers[o.metric_id] + " stderr"] = o.stderr
                except KeyError as e:
                    print("WTF, no {} in {}".format(o.metric_id, headers))
            yield ','.join([str(g)] + [ str(row[headers[k]]) for k in headers]) + '\n'

    headers={}
    if args['filename']:
        headers={'Content-Disposition': 'attachment; filename=' + args['filename']}
    return Response(generate(), mimetype='text/csv', headers=headers)

@app.route('/sites/<string:site_id>/archive_sql.csv')
def generate_archive_sql(site_id):
    args = parser.parse_args()
    metric_ids = [ int(mid) for mid in args['metrics'] ]
    filterexp = [Observation.site_id==site_id,Observation.offset_value == None]
    filterexp.append(Observation.metric_id.in_(metric_ids))
    filterexp.append(Observation.datetime.between(*args['interval']))
    if args['instrument']:
        filterexp.append(Observation.instrument_name==args['instrument'])
    
    def generate():
        print("generating query for metrics {} between {} and {}".format(metric_ids, *args['interval']))
        #q = db.session.query(\
        #                     func.date_trunc('minute',Observation.datetime)\
        #).select_from(Observation).\
        #    filter(*filterexp).\
        #    order_by(Observation.datetime.desc())
        mq = Metric.query.filter(Metric.id.in_(metric_ids))
        metrics = dict([ (m.id, " ".join([m.medium,m.name])) for m in mq ])
        headers = OrderedDict()
        for id in args['metrics']:
            headers[int(id)] = metrics[int(id)]
            if id.stderr:
                headers[str(id)] = metrics[int(id)] + " stderr"

        base_q = db.session.query(func.date_trunc('minute', Observation.datetime).label("datetime"), Observation.value, Observation.stderr, Observation.metric_id, Observation.offset_value).filter(*filterexp).order_by(Observation.datetime).subquery()
        #print("base_q columns: {}".format(base_q.c._all_columns))
        value_qs = [ db.session.query(base_q.c.datetime, base_q.c.value,base_q.c.stderr,base_q.c.offset_value).filter(base_q.c.metric_id==m,base_q.c.offset_value==None).order_by(base_q.c.datetime).subquery() for m in metric_ids]
        values = list(sum([ (vq.c.value,vq.c.stderr) for vq in value_qs ], ()))
        q = db.session.query(base_q, *values)

        for vq in value_qs:
            q = q.outerjoin(vq, base_q.c.datetime==vq.c.datetime)

            #print("value fields: {}".format(values))
        q = q.group_by(base_q.c.datetime, *values).order_by(base_q.c.datetime)
        for row in q:
            yield ",".join([ str(r) for r in row]) + "\n"
        ## SELECT o.datetime AS datetime,a.value,b.value FROM (SELECT date_trunc('minute', datetime) AS datetime,value,metric_id FROM observations WHERE datetime BETWEEN '2015-02-11' AND '2015-02-16') AS o LEFT JOIN (SELECT date_trunc('minute', datetime) AS datetime,value,metric_id FROM observations WHERE metric_id=6) a ON a.datetime=o.datetime LEFT JOIN (SELECT date_trunc('minute', datetime) AS datetime,value,metric_id FROM observations WHERE metric_id=14) b ON b.datetime=o.datetime
        
    return Response(generate(), mimetype='text/csv')
