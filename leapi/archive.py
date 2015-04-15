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

@app.route('/sites/<string:site_id>/archive.csv')
def generate_archive_sql(site_id):
    args = parser.parse_args()
    metric_ids = [ int(mid) for mid in args['metrics'] ]
    filterexp = [Observation.site_id==site_id,
                 Observation.metric_id.in_(metric_ids),
                 Observation.offset_value == 0,
                 Observation.datetime.between(*args['interval'])
             ]

    if args['instrument']:
        filterexp.append(Observation.instrument_name==args['instrument'])
    
    mq = Metric.query.filter(Metric.id.in_(metric_ids))
    metrics = dict([ (m.id, " ".join([m.medium,m.name])) for m in mq ])

    def clean_label(alabel):
        return alabel.replace('%', '%%')

    # build a base query that selects the requested metric_ids for the requested date range
    base_q = db.session.query(
        func.date_trunc('minute', Observation.datetime).label("datetime"), 
        Observation.value, Observation.stderr, 
        Observation.metric_id, 
        Observation.offset_value
    ).filter(*filterexp).order_by(Observation.datetime).subquery()

    def qlabels(mid):
        l = clean_label(metrics[int(mid)])
        v = [base_q.c.value.label(l)]
        if mid.stderr:
            v.append(base_q.c.stderr.label(l + ' stderr'))
            print("qvalue: {}".format(v))
        return v

    def qcolumns(vq, mid):
        l = clean_label(metrics[int(mid)])
        if mid.stderr:
            return (getattr(vq.c, l), getattr(vq.c, l + ' stderr'))
        else:
            return (getattr(vq.c, l),)

    # create a subquery for each of the metric id's, each will be a left outer join
    value_qs = [ db.session.query(base_q.c.datetime, *qlabels(m))\
                 .filter(base_q.c.metric_id==int(m),base_q.c.offset_value==0).subquery() for m in args['metrics'] ]
    # make a touble of query columns
    values = list(sum([ qcolumns(vq,mid) for vq, mid in zip(value_qs, args['metrics']) ], ()))

    # create the base query with all columns for requested metrics
    q = db.session.query(base_q.c.datetime, *values)

    # add a left join of each of the metric subqueries
    for vq in value_qs:
        q = q.outerjoin(vq, base_q.c.datetime==vq.c.datetime)

    # finally, group and order
    q = q.group_by(base_q.c.datetime, *values).order_by(base_q.c.datetime)

    def generate():
        yield ",".join([ d['name'].replace('%%','%') for d in q.column_descriptions]) + "\n"
        for row in q:
            yield ",".join([ str(r) for r in row]) + "\n"
        ## SELECT o.datetime AS datetime,a.value,b.value FROM (SELECT date_trunc('minute', datetime) AS datetime,value,metric_id FROM observations WHERE datetime BETWEEN '2015-02-11' AND '2015-02-16') AS o LEFT JOIN (SELECT date_trunc('minute', datetime) AS datetime,value,metric_id FROM observations WHERE metric_id=6) a ON a.datetime=o.datetime LEFT JOIN (SELECT date_trunc('minute', datetime) AS datetime,value,metric_id FROM observations WHERE metric_id=14) b ON b.datetime=o.datetime
        
    headers={}
    filename = "_until_".join([ dt.isoformat() for dt in args['interval']]) + ".csv"
    if args['instrument']:
        filename = args['instrument'] + "_" + filename
    if args['filename']:
        filename = args['filename']
    headers={'Content-Disposition': 'attachment; filename=' + filename}
    print("headers: {}".format(headers))
    return Response(generate(), mimetype='text/csv', headers=headers)
