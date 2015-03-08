from leapi.models import Metric,Observation,CountedMetric
from flask.ext.restplus import fields,abort
from leapi.hal import Resource
from leapi import db, api, hal
from sqlalchemy import func
from leapi import api

def add_count(obj,count):
    setattr(obj,'observationCount',count)
    return obj

def add_site(obj,site):
    setattr(obj,'site_id',site)
    return obj

metric_fields = api.model('Metric', {
    'id': fields.Integer(),
    'name': fields.String(description="name of the metric being observed, e.g. velocity, depth, voltage"),
    'medium': fields.String(description="the medium being observed, e.g. air, water, battery")
})

class MetricResource(Resource):
    fields = metric_fields
    
    _links = { 'timeseries': 'TimeseriesResource' }

    @hal.marshal_with(fields)
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


class CountedMetricResource(Resource):
    # Note, this depends on a view in teh database, SQLAlchemy
    # currently doesn't support the creation of a view, run this:

    # CREATE OR REPLACE VIEW counted_metrics AS SELECT
    # count(o.id),o.site_id,m.* FROM observations AS o RIGHT OUTER
    # JOIN variables AS m ON o.metric_id = m.id GROUP BY
    # m.id,o.site_id;
    fields = api.extend('CountedMetric', metric_fields, {
        'observationCount': fields.Integer(attribute='count', description="Number of observations made on this metric")
    })

    link_args = ['site_id', ('metric_id', 'id')]

    _links = { 'timeseries': ('TimeseriesResource', {'metric_id': 'id'}) }

    @hal.marshal_with(fields, links=_links)
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
