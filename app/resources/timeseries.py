from flask import request

from app import db
from app.models import Observation,Site,Sensor,Metric,Unit,Instrument

from sqlalchemy.exc import IntegrityError,DataError

from flask.ext.restful import fields
from flask.ext.restful import reqparse
from flask.ext.restful import abort

from app.hal import HalResource, marshal_with

class TimeseriesResource(HalResource):
    
    def get(self, site_id):
        data = []
        if 'metric' in ( k.split('.')[0] for k in request.args.keys() ):
            mkeys = [ k.split('.')[1] for k in request.args.keys() if k.split('.')[0] == 'metric' ]
            filter_by = dict([ (k.split('.')[1], v) for k,v in request.args.items() if k.split('.')[0] == 'metric' ])
            r = Observation.query.join(Observation.metric).filter_by(**filter_by).limit(200).all()
            data = [ (ob.value, str(ob.datetime)) for ob in r ]
            return dict(data=data,metric=filter_by)
        return dict(data=data)
