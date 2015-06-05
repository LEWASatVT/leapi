from flask.ext.restplus import fields,abort

from leapi import api,hal
from leapi.models import Flag
from leapi.hal import Resource

flag_fields = api.model('Flag', {
    'id': fields.Integer,
    'name': fields.String,
    'description': fields.String
    })

class FlagList(Resource):
    fields = flag_fields
    
    @hal.marshal_with(fields, as_list=True)
    def get(self,site_id):
        return Flag.query.all()
