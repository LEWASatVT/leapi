from app.models import Instrument
from app.hal import HalResource, marshal_with
from flask.ext.restful import fields
from flask.ext.restful import marshal_with

class InstrumentResource(HalResource):
    fields = {
        'id': fields.Integer,
        'name': fields.String,
        'manufacturer': fields.String,
        'model': fields.String,
        'site_id': fields.String
    }

    _embedded = ['site']

    @marshal_with(fields)
    def get(self, id = None):
        if id == None:
            r = Instrument.query.all()
        else:
            r = Instrument.query.get_or_404(id)
        return r
