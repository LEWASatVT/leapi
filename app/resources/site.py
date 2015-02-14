from app.models import Site
from flask.ext.restful import Resource
from flask.ext.restful import fields
from flask.ext.restful import marshal_with

site_fields = {
    'id': fields.String,
    'name': fields.String
}

class SiteResource(Resource):
    @marshal_with(site_fields)
    def get(self, id = None):
        if id == None:
            site = Site.query.all()
        else:
            site = Site.query.get_or_404(id)
        return site
