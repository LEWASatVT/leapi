from app.models import Instrument
from flask.ext.restful import Resource
from flask.ext.restful import fields
from flask.ext.restful import marshal_with

fields = {
    'id': fields.Integer,
    'name': fields.String,
    'manufacturer': fields.String,
    'model': fields.String,
    'site_id': fields.String
}

class InstrumentResource(Resource):
    @marshal_with(fields)
    def get(self, id = None):
        if id == None:
            r = Instrument.query.all()
        else:
            r = Instrument.query.get_or_404(site_id)
        return r
