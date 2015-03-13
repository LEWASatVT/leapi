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

parser = api.parser()
parser.add_argument('metrics', type=inputList(inputs.natural), required=True, help="list of metric id's to include in archive", location='args')
parser.add_argument('interval', type=inputs.iso8601interval, required=True, help="iso8601 formated time interval", location='args')

##TODO print header row
@app.route('/sites/<string:site_id>/archive.csv')
def generate_archive(site_id):
    args = parser.parse_args()
    
    filterexp = [Observation.site_id==site_id,Observation.offset_value == None]

    filterexp.append(Observation.metric_id.in_(args['metrics']))
    filterexp.append(Observation.datetime.between(*args['interval']))

    def generate():
        print("performing query between {}".format(args['interval']))
        #q = db.session.query(\
        #                     func.date_trunc('minute',Observation.datetime)\
        #).select_from(Observation).\
        #    filter(*filterexp).\
        #    order_by(Observation.datetime.desc())
        mq = Metric.query.filter(Metric.id.in_(args['metrics']))
        metrics = dict([ (m.id, " ".join([m.medium,m.name])) for m in mq ])
        headers = OrderedDict()
        for id in args['metrics']:
            headers[id] = metrics[id]
            
        print("using headers: {}".format(headers.keys()))
        q = Observation.query.filter(*filterexp).order_by(Observation.datetime.desc())
        yield ",".join(['datetime'] + headers.values()) + "\n"


        ## SELECT o.datetime AS datetime,a.value,b.value FROM (SELECT date_trunc('minute', datetime) AS datetime,value,metric_id FROM observations WHERE datetime BETWEEN '2015-02-11' AND '2015-02-16') AS o LEFT JOIN (SELECT date_trunc('minute', datetime) AS datetime,value,metric_id FROM observations WHERE metric_id=6) a ON a.datetime=o.datetime LEFT JOIN (SELECT date_trunc('minute', datetime) AS datetime,value,metric_id FROM observations WHERE metric_id=14) b ON b.datetime=o.datetime
        
        def float_or_nan(value=None):
            if value is not None:
                return float(value)
            else:
                return 'ND'
        
        for g,k in itertools.groupby(q, lambda a: datetime(a.datetime.year,a.datetime.month,a.datetime.day,a.datetime.hour,a.datetime.minute)):
            row = defaultdict(float_or_nan)
            #row = list(k)
            #row = dict([ ("{} {}".format(o.metric.medium, o.metric.name), o.value) for o in row ])
            for o in k:
                try:
                    row[headers[o.metric_id]] = o.value
                except KeyError as e:
                    print("WTF, no {} in {}".format(o.metric_id, headers))
            yield ','.join([str(g)] + [ str(row[headers[k]]) for k in headers]) + '\n'

    return Response(generate(), mimetype='text/csv')
