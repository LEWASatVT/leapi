from leapi import db
from leapi.models import Unit

from flask.ext.restful import fields

from leapi.hal import HalResource, marshal_with

class UnitResource(HalResource):
    fields = {
        'id' : fields.Integer,
        'abbv': fields.String,
        'name': fields.String,
        'type': fields.String
    }

    @marshal_with(fields)
    def get(self, id = None):
        if id == None:
            r = Unit.query.all()
        else:
            r = Unit.query.get_or_404(id)
        return r
