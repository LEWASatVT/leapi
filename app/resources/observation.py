from flask import request

from app.models import Observation,Sensor,Metric
from flask.ext.restful import Resource
from flask.ext.restful import fields
from flask.ext.restful import marshal_with
from flask.ext.restful import reqparse

fields = {
    'id': fields.Integer,
    'datetime': fields.DateTime,
    'value': fields.Float,
    'variable_id': fields.Integer,
    'unit_id': fields.Integer
}

parser = reqparse.RequestParser()
parser.add_argument('value', type=float)
parser.add_argument('datetime', type=str)
parser.add_argument('units', type=str)
parser.add_argument('site_id', type=str)

class ObservationResource(Resource):
    @marshal_with(fields)
    def get(self, id = None):
        if id == None:
            r = Observation.query.all()
        else:
            r = Observation.query.get_or_404(site_id)
        return r

    def post(self):
        args = parser.parse_args()
        r = Observation(datetime=args['datetime'], value=args['value'], units=args['units'])
        return r, 201
