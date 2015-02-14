from app.models import Sensor,Instrument,Metric
from flask.ext.restful import Resource
from flask.ext.restful import fields
from flask.ext.restful import marshal_with

fields = {
    'id': fields.Integer,
    'name': fields.String,
    'instrument_id': fields.Integer,
    'variable_id': fields.Integer
}

class SensorResource(Resource):
    @marshal_with(fields)
    def get(self, id = None):
        if id == None:
            r = Sensor.query.all()
        else:
            r = Sensor.query.get_or_404(site_id)
        return r
