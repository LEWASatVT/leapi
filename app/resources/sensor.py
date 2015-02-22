from app.models import Sensor,Instrument,Site,Metric
from flask.ext.restful import fields
from json import dumps

from app.hal import HalResource, marshal_with

fields = {
    'id': fields.Integer,
    'name': fields.String,
    '_embedded': { 'metric': fields.Nested( { 'medium': fields.String, 'name': fields.String } ),
                   'instrument': fields.Nested( {'id': fields.Integer, 'name': fields.String} )
                   }
}

class SensorResource(HalResource):
    @marshal_with(fields)
    def get(self, site_id, instrument_name, id = None):
        print("getting sensors for {} at {}".format(instrument_name,site_id))
        q = Sensor.query.join(Sensor.instrument,Site).filter(Site.id==site_id,Instrument.name==instrument_name)
        if id == None:
            r = q.all()
        else:
            print("getting sensors for {} at {}".format(instrument_name,site_id))
            r = Sensor.query.get_or_404(id)
        return r
