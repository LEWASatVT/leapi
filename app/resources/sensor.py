from app.models import Sensor,Instrument,Metric
from flask.ext.restful import Resource
from flask.ext.restful import fields
from flask.ext.restful import marshal_with
from json import dumps
from flask.ext.restful import marshal

fields = {
    'id': fields.Integer,
    'name': fields.String,
    '_embedded': { 'metric': fields.Nested( { 'medium': fields.String, 'name': fields.String } ),
                   'instrument': fields.Nested( {'id': fields.Integer, 'name': fields.String} )
                   }
}

class SensorResource(Resource):
    @marshal_with(fields)
    def get(self, id = None):
        if id == None:
            r = Sensor.query.all()
        else:
            r = Sensor.query.get_or_404(site_id)
        return r
