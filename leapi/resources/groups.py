#from string import maketrans
import re

from flask.ext.restplus import fields, abort

from leapi.models import Group, Instrument, Metric
from leapi import api, hal
from leapi.hal import Resource
from leapi.resources.metric import metric_fields

group_fields = api.model('group', 
                         {
                             'id': fields.Integer(),
                             'name': fields.String(),
                             'parent_id': fields.Integer()
                         })

self_link = api.model('self', 
                      {
                          'href': fields.Url('metricresource')
                      })

metric_links = api.model('metriclinks',
                         { 'self': fields.Nested(self_link),
                           'timeseries': fields.Nested(api.model('timeseries', { 'href': fields.Url('timeseriesresource') }))
                         })

_embedded = { 'metrics': api.extend('hal_metrics', metric_fields, 
                                    { 
                                        #'_links': fields.Url('metricresource')
                                        '_links': fields.Nested(metric_links)
                                    })
          }

def _populate_metricgroup_links(r, site_id):
    for m in r.metrics:
        #setattr(m, '_links', {'self': {'href': {'site_id': site_id, 'id': m.id}}})
        mylinkdata = {}
        for t in ['self','timeseries']:
            mylinkdata[t] = {'site_id': site_id, 'metric_id': m.id, 'id': m.id}
        setattr(m, '_links', mylinkdata)


def name_filter(s):
    # For some reason str.translate(string.maketrans(' ', '_'))
    # generated errors
    return re.sub(r'\s+',r'_', s.lower())

@api.doc(description='Describes a group of metrics, e.g. water quality metrics of pH, dissolved oxygen, etc.')
class MetricGroup(Resource):
    """A group of metrics"""

    fields = group_fields

    @hal.marshal_with(group_fields, embedded=_embedded, as_list=True)
    def get(self,site_id, name=None, id=None):
        """Get a single metric group"""
        filters = [Group.site_id==site_id]
        if id is not None:
            filters.append(Group.id==id)

        q = Group.query.filter(*filters)
        g = []
        if name is not None:
            for grp in q.all():
                print("does {} == {}?".format(name_filter(grp.name), name))

            g = [ g for g in q.all() if name_filter(g.name) == name ]
            g = g[0] if g else None
        else:
            g = q.first()

        if not g:
            abort(404)
        _populate_metricgroup_links(g, site_id)
        return g

class MetricGroupList(Resource):
    """A list of metric groups"""

    @hal.marshal_with(group_fields, embedded=_embedded, as_list=True)
    def get(self, site_id):
        """Get a list of metric groups"""
        q = Group.query.filter(Group.site_id==site_id)
        l = q.all()
        for r in l:
            _populate_metricgroup_links(r, site_id)
        return l
