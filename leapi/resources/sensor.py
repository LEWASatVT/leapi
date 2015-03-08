from leapi import api, hal
from leapi.models import Sensor,Instrument,Site,Metric,Unit
from flask.ext.restful import fields, Resource
from json import dumps

@api.doc(False)
class SensorResource(Resource):
    fields = api.model('Sensor', {
        'id': fields.Integer,
        'name': fields.String,
    })

    link_args = ['site_id','instrument_name']
    #_links = { 'instrument': HalLink('InstrumentResource', ['site_id', ('instrument_id','id')]) }
    _embedded = [ ('metric','CountedMetricResource') ]

    @hal.marshal_with(fields)
    def get(self, site_id, instrument_name, id = None):
        q = Sensor.query.join(Sensor.instrument,Site).filter(Site.id==site_id,Instrument.name==instrument_name)
        if id == None:
            r = q.all()
        else:
            r = Sensor.query.get_or_404(id)
        setattr(r,'site_id',site_id)
        setattr(r,'instrument_name',r.instrument.name)
        return r
