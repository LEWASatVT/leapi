from flask import request

from app import db
from app.models import Observation,Site,Sensor,Metric,Unit

from sqlalchemy.exc import IntegrityError,DataError

from flask.ext.restful import Resource
from flask.ext.restful import fields
from flask.ext.restful import reqparse
from flask.ext.restful import abort

from app.hal import HalResource, marshal_with

fields = {
    'id': fields.Integer,
    'datetime': fields.DateTime,
    'value': fields.Float,
    'site_id': fields.String,
    '_embedded': { 'units': fields.Nested ( { 'id': fields.Integer, 'abbv': fields.String, 'name': fields.String }),
                   'metric': fields.Nested ( { 'id': fields.Integer, 'name': fields.String, 'medium': fields.String }),
                   'sensor': fields.Nested ( { 'name': fields.String } )
                   },
}

parser = reqparse.RequestParser()
parser.add_argument('value', type=float, required=True, help="value cannot be blank")
parser.add_argument('datetime', type=str, required=True, help="missing datetime")
parser.add_argument('units', type=str, required=True, help="missing units")
parser.add_argument('sensor_id', type=int, required=True, help="missing sensor id")
parser.add_argument('metric_id', type=int, required=True, help="missing metric id")
parser.add_argument('site_id', type=str, required=True, help="missing site_id")

class ObservationResource(HalResource):
    @marshal_with(fields)
    def get(self, id = None):
        if id == None:
            r = Observation.query.all()
        else:
            r = Observation.query.get_or_404(id)
        return r

    @marshal_with(fields)
    def post(self):
        if not request.json:
            abort(400, message="request must be JSON")
        errors = []
        print("json: {}".format(request.json))
        args = parser.parse_args(request)
        r = Observation(datetime=args['datetime'], value=args['value'], units=args['units'])
        site = Site.query.get(args['site_id'])
        sensor = Sensor.query.get(args['sensor_id'])
        metric = Metric.query.get(args['metric_id'])
        unit = Unit.query.filter_by(abbv=args['units']).first()
        if site == None:
            errors.append("No site with id: {}".format(args['site_id']))
        if unit == None:
            errors.append("No unit with abbv: {}".format(args['units']))
        if sensor == None:
            errors.append("No sensor with id: {}".format(args['sensor_id']))
        if metric == None:
            errors.append("No metric with id: {}".format(args['metric_id']))

        if len(errors) > 0:
            return dict(messages=errors), 400
        r.site_id = site.id
        r.site = site
        r.sensor = sensor
        r.sensor_id = sensor.id
        r.metric = metric
        r.metric_id = metric.id
        r.units = unit
        db.session.add(r)
        try:
            db.session.commit()
        except DataError, e:
            abort(400, message=dict(data_error=e.message))
        except IntegrityError, e:
            abort(409, message=dict(integrity_error=e.message))
        return r, 201
