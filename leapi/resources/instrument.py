from leapi import api, hal
from leapi.models import Instrument,Site
from leapi.hal import Resource
import flask.ext.restplus as restful

fields = {
    'id': restful.fields.Integer(),
    'name': restful.fields.String(),
    'manufacturer': restful.fields.String(),
    'model': restful.fields.String(),
    'site_id': restful.fields.String()
}

class InstrumentResource(Resource):
    fields = api.model('Instrument', fields)

    link_args = ['site_id']

    #_embedded = ['site', ('sensors','SensorResource')]

    def __init__(self):
        self.parser = api.parser()
        self.parser.add_argument('name', type=str)
        super(InstrumentResource,self).__init__()


    @hal.marshal_with(fields)
    def get(self, site_id, name = None):
        '''list instruments at a particular site'''
        args = self.parser.parse_args()
        filterexp=[Site.id==site_id]
        if args['name']:
            if not site_id:
                abort(400, message="must use /sites/<site_id>/instruments to query instruments")
            filterexp.append(Instrument.name==args['name'])    

        q = Instrument.query
        
        if name == None:
            r = q.join(Site).filter(*filterexp).all()
        else:
            r = q.get_or_404([site_id,name])
        return r
