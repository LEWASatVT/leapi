from app.models import Site
from flask.ext.restful import Resource
from flask.ext.restful import fields
from flask.ext.restful import marshal_with

class Embedded(fields.Raw):
    def output(self, key, obj):
        print("key: {}, obj: {}".format(key,type(obj)))
        return dict(instruments=[ dict(id=i.id, name=i.name) for i in obj.instruments ])

site_fields = {
    'id': fields.String,
    'name': fields.String,
    '_embedded': Embedded
}

class SiteResource(Resource):
    @marshal_with(site_fields)
    def get(self, id = None):
        if id == None:
            site = Site.query.all()
        else:
            site = Site.query.get_or_404(id)
        return site

class SiteList(Resource):
    @marshal_with(site_fields, envelope='sites')
    def get(self):
        return Site.query.all()
