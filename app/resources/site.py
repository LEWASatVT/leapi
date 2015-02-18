from app.models import Site
from flask.ext.restful import Resource
from flask.ext.restful import fields
from app.hal import HalResource, marshal_with

class SiteResource(HalResource):
    fields = {
        'id': fields.String,
        'name': fields.String,
    }
    #_embedded = ['instruments']

    @marshal_with(fields)
    def get(self, id = None):
        if id == None:
            site = Site.query.all()
        else:
            site = Site.query.get_or_404(id)
        return site

class SiteList(HalResource):
    @marshal_with(SiteResource.fields, envelope='sites')
    def get(self):
        return Site.query.all()
