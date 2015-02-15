from app.models import Site
from flask.ext.restful import Resource
from flask.ext.restful import fields
from app.hal import HalResource, marshal_with

class Embedded(fields.Raw):
    def output(self, key, obj):
        print("key: {}, obj: {}".format(key,type(obj)))
        return dict(instruments=[ dict(id=i.id, name=i.name) for i in obj.instruments ])

site_fields = {
    'id': fields.String,
    'name': fields.String,
    '_embedded': Embedded
}

class SiteResource(HalResource):
    _embedded = ['instruments']

    @marshal_with(site_fields)
    def get(self, id = None):
        if id == None:
            site = Site.query.all()
        else:
            site = Site.query.get_or_404(id)
        return site

class SiteList(HalResource):
    @marshal_with(site_fields, envelope='sites')
    def get(self):
        return Site.query.all()
