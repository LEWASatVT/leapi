from app.models import Metric
from flask.ext.restful import fields
from app.hal import HalResource, marshal_with

fields = {
    'id': fields.Integer,
    'name': fields.String,
    'medium': fields.String
}

class MetricResource(HalResource):
    @marshal_with(fields)
    def get(self, id = None):
        if id == None:
            r = Metric.query.all()
        else:
            r = Metric.query.get_or_404(site_id)
        return r
