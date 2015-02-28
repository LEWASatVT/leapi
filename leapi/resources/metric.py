from leapi.models import Metric,Observation,CountedMetric
from flask.ext.restful import fields,abort
from leapi.hal import HalResource, marshal_with, HalLink
from leapi import db
from sqlalchemy import func
from leapi import api

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

    _links = { 'timeseries': HalLink('TimeseriesResource', ['site_id', ('id', 'metric.id')]) }

    @marshal_with(fields)
    def get(self, site_id=None, id=None):
        filters=[]
        if site_id:
            filters.append(Observation.site_id==site_id)
        if id:
            filters.append(Metric.id==id)
        
        q = db.session.query(Metric,func.count()).outerjoin(Observation)
        if len(filters):
            q = q.filter(*filters)
        q = q.group_by(Metric)

        if id == None:
            # count how many observations each metric has associated with it
            r = q.all()
            r = [ add_count(m,c) for (m,c) in r ]
        else:
            if not q.first():
                abort(404)
            r = add_count(*(q.first()))
            
        if site_id:    
            if hasattr(r, '__iter__'):
                r = [ add_site(m,site_id) for m in r ]
            else:
                r = add_site(r,site_id)
        return r


class CountedMetricResource(HalResource):
    # Note, this depends on a view in teh database, SQLAlchemy
    # currently doesn't support the creation of a view, run this:

    # CREATE OR REPLACE VIEW counted_metrics AS SELECT
    # count(o.id),o.site_id,m.* FROM observations AS o RIGHT OUTER
    # JOIN variables AS m ON o.metric_id = m.id GROUP BY
    # m.id,o.site_id;
    fields = {
        'id': fields.Integer,
        'name': fields.String,
        'medium': fields.String,
        'observationCount': fields.Integer(attribute='count')
    }

    link_args = ['site_id', ('metric_id', 'id')]

    _links = { 'timeseries': HalLink('TimeseriesResource', ['site_id', ('id', 'metric_id')]) }

    @marshal_with(fields)
    def get(self, site_id=None, id=None):
        filters=[]
        if site_id:
            filters.append(CountedMetric.site_id==site_id)
        if id:
            filters.append(CountedMetric.id==id)
        
        q = CountedMetric.query
        if len(filters):
            q = q.filter(*filters)

        if id == None:
            # count how many observations each metric has associated with it
            r = q.all()
            r = [ m for m in r ]
        else:
            if not q.first():
                abort(404)
            r = q.first()
            setattr(r, 'site_id',site_id)
        return r
