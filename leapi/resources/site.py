from leapi.models import Site,Instrument
from leapi.resources import instrument
from leapi import api, hal
import flask.ext.restplus as restful
from leapi.hal import Resource

#TODO: do this stuff in HalResource

site_fields = {
        'id': restful.fields.String(description="ID of site"),
        'name': restful.fields.String(description="A descriptive name of the site"),
    #'_links': {'self': {'href': restful.fields.Url('siteresource')}}
    #'_embedded': restful.fields.Nested(embedded, description="embedded resources")
}


class SiteResource(Resource):
    fields = api.model('Site', site_fields)
    
    _embedded = {'instruments': [instrument.InstrumentResource.fields] }

    _links = { 'metrics': ('CountedMetricResource',  {'site_id': 'id'}),
               'instruments': ('InstrumentResource', {'site_id': 'id'})
           }

    link_args = {'site_id': 'id'}
    
    @hal.marshal_with(fields, embedded=_embedded, links=_links)
    def get(self, id = None):
        '''get a particular site or list of sites'''
        if id == None:
            site = Site.query.join(Instrument).all()
        else:
            site = Site.query.get_or_404(id)
        return site

class SiteList(Resource):
    fields = api.model('Site', site_fields)

    _embedded = {'instruments': [instrument.fields] }

    @hal.marshal_with(fields, envelope='sites')
    def get(self,id=None):
        if id == None:
            site = Site.query.join(Instrument).all()
        else:
            site = Site.query.get_or_404(id)
            setattr(site, 'instruments', site.instruments.all())
        return site

