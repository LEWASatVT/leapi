from leapi import db, api, hal
from leapi.models import Unit

from flask.ext.restplus import fields, Resource

@api.doc(False)
class UnitResource(Resource):
    fields = api.model('Unit', {
        'id' : fields.Integer(),
        'abbv': fields.String(),
        'name': fields.String(),
        'type': fields.String()
    })

    @hal.marshal_with(fields)
    def get(self, id = None):
        if id == None:
            r = Unit.query.all()
        else:
            r = Unit.query.get_or_404(id)
        return r
