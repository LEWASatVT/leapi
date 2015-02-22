from app.models import Instrument,Site
from app.hal import HalResource, marshal_with
from flask.ext.restful import fields
from flask.ext.restful import marshal_with
from flask.ext.restful import reqparse

class InstrumentResource(HalResource):
    fields = {
        'id': fields.Integer,
        'name': fields.String,
        'manufacturer': fields.String,
        'model': fields.String,
        'site_id': fields.String
    }

    _embedded = ['site']

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('name', type=str)
        super(InstrumentResource,self).__init__()


    @marshal_with(fields)
    def get(self, site_id, id = None):
        args = self.parser.parse_args()
        if args['name']:
            if not site_id:
                abort(400, message="must use /sites/<site_id>/instruments to query instruments")
            q = Instrument.query.join(Site).filter(Site.id==site_id,Instrument.name==args['name'])
            return q.all()
        if id == None:
            r = Instrument.query.all()
        else:
            r = Instrument.query.get_or_404(id)
        return r
