from flask import request

from app.models import Observation,Site,Sensor,Metric,Unit,Instrument
#from app.resources import MetricResource,UnitResource
#from app import resources as res

from sqlalchemy.exc import IntegrityError,DataError

from flask.ext.restful import fields
from flask.ext.restful import reqparse
from flask.ext.restful import abort
from flask.ext.restful import marshal

from app.hal import HalResource, marshal_with
from app import api

import pytz
TZ = pytz.timezone('US/Eastern')
class TimeseriesResource(HalResource):
    fields = {
        'length': fields.Integer,
        'data': fields.Raw
    }

    link_args = [ 'site_id' ]

    _embedded = [ 'metric',
                  ('units', 'UnitResource')
              ]

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('metric.id', type=int)
        self.parser.add_argument('metric.name', type=str)
        self.parser.add_argument('metric.medium', type=str)
        super(TimeseriesResource,self).__init__()

    @marshal_with(fields)
    def get(self, site_id):
        #print("my endpoint is {}".format(self.endpoint))
        #print("my url is {}".format(api.url_for(self, site_id='stroubles1')))
        data = []
        args = self.parser.parse_args()
        if args['metric.id'] == None and (args['metric.medium'] == None or args['metric.name'] == None):
            abort(400, status=400, message="must supply either metric.id OR metric.name AND metric.medium")

        #TODO: based on use of parse_args above, can probably clean
        #this up. Remember, argparse can have differnet
        #internal/external names too, which could be handy
        if 'metric' in ( k.split('.')[0] for k in request.args.keys() ):
            mkeys = [ k.split('.')[1] for k in request.args.keys() if k.split('.')[0] == 'metric' ]
            filter_by = dict([ (k.split('.')[1], v) for k,v in request.args.items() if k.split('.')[0] == 'metric' ])
            r = Observation.query.join(Observation.metric).filter_by(**filter_by).order_by(Observation.datetime.desc()).limit(1440).all()
            print("len(r): {}".format(len(r)))
            if len(r) > 0:
                units = list(set([ o.units for o in r]))[0]
                metric = list(set([ o.metric for o in r]))[0]
                data = [ (ob.value, ob.datetime.isoformat()) for ob in r ]
                return dict(data=data,metric=metric,units=units,site_id=site_id,length=len(r))
        return dict(data=data,length=0)
