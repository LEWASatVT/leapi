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
        'data': fields.Raw
    }

    link_args = [ 'site_id' ]

    _embedded = [ 'metric',
                  ('units', 'UnitResource')
              ]

    @marshal_with(fields)
    def get(self, site_id):
        #print("my endpoint is {}".format(self.endpoint))
        #print("my url is {}".format(api.url_for(self, site_id='stroubles1')))
        data = []
        if 'metric' in ( k.split('.')[0] for k in request.args.keys() ):
            mkeys = [ k.split('.')[1] for k in request.args.keys() if k.split('.')[0] == 'metric' ]
            filter_by = dict([ (k.split('.')[1], v) for k,v in request.args.items() if k.split('.')[0] == 'metric' ])
            r = Observation.query.join(Observation.metric).filter_by(**filter_by).order_by(Observation.datetime.desc()).limit(1440).all()
            units = list(set([ o.units for o in r]))[0]
            metric = list(set([ o.metric for o in r]))[0]
            data = [ (ob.value, ob.datetime.isoformat()) for ob in r ]
            return dict(data=data,metric=metric,units=units,site_id=site_id)
        return dict(data=data)
