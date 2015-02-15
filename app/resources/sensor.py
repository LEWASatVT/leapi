from app.models import Sensor,Instrument,Metric
from flask.ext.restful import fields
from json import dumps

from app.hal import HalResource, marshal_with

fields = {
    'id': fields.Integer,
    'name': fields.String,
    '_embedded': { 'metric': fields.Nested( { 'medium': fields.String, 'name': fields.String } ),
                   'instrument': fields.Nested( {'id': fields.Integer, 'name': fields.String} )
                   }
}

class SensorResource(HalResource):
    @marshal_with(fields)
    def get(self, id = None):
        if id == None:
            r = Sensor.query.all()
        else:
            r = Sensor.query.get_or_404(site_id)
        return r
