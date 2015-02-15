from app import db
from app.models import Unit

from flask.ext.restful import Resource
from flask.ext.restful import fields
from flask.ext.restful import marshal_with

fields = {
    'abbv': fields.String,
    'name': fields.String,
    'type': fields.String
}

class UnitResource(Resource):
    @marshal_with(fields)
    def get(self, id = None):
        if id == None:
            r = Unit.query.all()
        else:
            r = Unit.query.get_or_404(id)
        return r
