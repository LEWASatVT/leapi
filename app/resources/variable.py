from app.models import Metric
from flask.ext.restful import Resource
from flask.ext.restful import fields
from flask.ext.restful import marshal_with

fields = {
    'id': fields.Integer,
    'name': fields.String,
    'medium': fields.String
}

class VariableResource(Resource):
    @marshal_with(fields)
    def get(self, id = None):
        if id == None:
            r = Metric.query.all()
        else:
            r = Metric.query.get_or_404(site_id)
        return r
