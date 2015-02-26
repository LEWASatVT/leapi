from app.models import Site,Instrument
from flask.ext.restful import Resource
from flask.ext.restful import fields
from app.hal import HalResource, HalLink, marshal_with

site_fields = {
        'id': fields.String,
        'name': fields.String,
    }

class SiteResource(HalResource):
    fields = site_fields

    _embedded = ['instruments']

    @marshal_with(fields)
    def get(self, id = None):
        if id == None:
            site = Site.query.all()
        else:
            site = Site.query.get_or_404(id)
            print("site instruments: {}".format(type(site.instruments)))
        return site

class SiteList(HalResource):
    fields = site_fields

    _links = { 'metrics': HalLink('CountedMetricResource', [('id','site_id')]),
               'instruments': HalLink('InstrumentResource', [('id', 'site_id')])
           }

    _embedded = [('instruments','InstrumentResource')]
    
    @marshal_with(SiteResource.fields, envelope='sites')
    def get(self,id=None):
        if id == None:
            site = Site.query.join(Instrument).all()
        else:
            site = Site.query.get_or_404(id)
            setattr(site, 'instruments', site.instruments.all())
        return site

