from app.models import Metric,Observation
from flask.ext.restful import fields
from app.hal import HalResource, marshal_with, HalLink
from app import db
from sqlalchemy import func
from app import api

def add_count(obj,count):
    setattr(obj,'observationCount',count)
    return obj

def add_site(obj,site):
    setattr(obj,'site_id',site)
    return obj

class MetricResource(HalResource):
    fields = {
        'id': fields.Integer,
        'name': fields.String,
        'medium': fields.String,
        'observationCount': fields.Integer
    }

    _links = { 'timeseries': HalLink('TimeseriesResource', ['site_id','id']) }

    @marshal_with(fields)
    def get(self, id = None):
        if id == None:
            # count how many observations each metric has associated with it
            r = db.session.query(Metric,func.count()).outerjoin(Observation).group_by(Metric).all()
            print("r: {}".format(r))
            r = [ add_count(m,c) for (m,c) in r ]
            print("r: {}".format(r))
        else:
            #r = db.session.query(Metric,func.count()).join(Observation).group_by(Metric).filter_by(id=id).first()
            r = Metric.query.get_or_404(id)
        if hasattr(r, '__iter__'):
            r = [ add_site(m,'stroubles1') for m in r ]
        else:
            r = add_site(r,'stroubles1')
        return r
