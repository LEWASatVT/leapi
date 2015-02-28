from flask import request
import itertools

from leapi.models import Observation,Site,Sensor,Metric,Unit,Instrument,CountedMetric
#from app.resources import MetricResource,UnitResource
#from app import resources as res

from sqlalchemy.exc import IntegrityError,DataError

from flask.ext.restful import fields
from flask.ext.restful import reqparse
from flask.ext.restful import abort
from flask.ext.restful import marshal

from leapi.hal import HalResource, marshal_with
from leapi import api

import pytz
from leapi.dateparser import DateParser

TZ = pytz.timezone('US/Eastern')

def make_ts(r,instrument_id,site_id):
    units = list(set([ o.units for o in r]))[0]
    metric = list(set([ o.metric for o in r]))[0]
    data = [ (ob.value, ob.datetime.isoformat()) for ob in r ]
    instrument = Instrument.query.get(instrument_id)
    for o in [ metric, instrument ]:
        setattr(o,'site_id',site_id)
    return dict(data=data,instrument=instrument,metric=metric,metric_id=metric.id,units=units,site_id=site_id,length=len(data))

class TimeseriesResource(HalResource):
    
    fields = {
        'length': fields.Integer,
        'data': fields.Raw
    }

    link_args = [ 'site_id', 'metric_id' ]

    _embedded = [ ('metric', 'CountedMetricResource'),
                  ('units', 'UnitResource'),
                  ('instrument')
              ]

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('metric.id', type=int)
        self.parser.add_argument('metric.name', type=str)
        self.parser.add_argument('metric.medium', type=str)
        self.parser.add_argument('since', type=str)
        self.parser.add_argument('limit', type=int)
        self.dateparser =  DateParser()

        super(TimeseriesResource,self).__init__()

    @marshal_with(fields)
    def get(self, site_id, metric_id=None):
        #print("my endpoint is {}".format(self.endpoint))
        #print("my url is {}".format(api.url_for(self, site_id='stroubles1')))
        data = []
        filterexp = [Site.id==site_id,Observation.site_id==Site.id,Observation.instrument_id==Instrument.id, Observation.offset_value == None]

        args = self.parser.parse_args()
        if metric_id == None and (args['metric.id'] == None and (args['metric.medium'] == None or args['metric.name'] == None)):
            abort(400, status=400, message="must supply either metric.id OR metric.name AND metric.medium")

        metric_id = metric_id if metric_id else args['metric.id']
        if metric_id:
            filterexp.append(Metric.id==metric_id)
        elif 'metric' in ( k.split('.')[0] for k in request.args.keys() ):
            mkeys = [ k.split('.')[1] for k in request.args.keys() if k.split('.')[0] == 'metric' ]
            filter_by = dict([ (k.split('.')[1], v) for k,v in request.args.items() if k.split('.')[0] == 'metric' ])
            for k,v in filter_by.items():
                filterexp.append(getattr(Observation,"metric_"+k)==v)

        if not args['since']:
            yesterday = self.dateparser.parse('1 day')
            filterexp.append(Observation.datetime>=yesterday)
        else:
            d = self.dateparser.parse(args['since'])
            if d:
                filterexp.append(Observation.datetime>=d)
            else:
                abort(400, message="Could not parse date expression: '{}'".format(args['since']))

        #TODO: based on use of parse_args above, can probably clean
        #this up. Remember, argparse can have differnet
        #internal/external names too, which could be handy
        q = Observation.query.join(Observation.metric,Site,Instrument).filter(*filterexp).order_by(Observation.instrument_id,Observation.datetime.desc()).group_by(Observation.instrument_id,Observation.id)
        if args['limit']:
            q = q.limit(args['limit'])
        r = q.all()
                    
        grp = [ make_ts(list(k),g,site_id) for g,k in itertools.groupby(r,lambda x: x.instrument_id) ]
        grp = grp[0] if len(grp)==1 else grp
        return grp
