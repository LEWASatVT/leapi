from flask.ext.restplus import fields

from leapi.models import Group, Instrument, Metric
from leapi import api, hal
from leapi.hal import Resource
from leapi.resources.metric import metric_fields

group_fields = api.model('group', 
                         {
                             'name': fields.String(),
                         })

class MetricGroup(Resource):
    """A group of metrics"""

    def get(self,site_id,id):
        pass

self_link = api.model('self', 
                      {
                          'href': fields.Url('metricresource')
                      })

metric_links = api.model('metriclinks',
                         { 'self': fields.Nested(self_link),
                           'timeseries': fields.Nested(api.model('timeseries', { 'href': fields.Url('timeseriesresource') }))
                         })

class MetricGroupList(Resource):
    """A list of metric groups"""

    _embedded = { 'metrics': api.extend('hal_metrics', metric_fields, 
                                        { 
                                            #'_links': fields.Url('metricresource')
                                            '_links': fields.Nested(metric_links)
                                        })
                  }

    @hal.marshal_with(group_fields, embedded=_embedded, as_list=True)
    def get(self, site_id):
        q = Group.query.filter(Group.site_id==site_id)
        l = q.all()
        for r in l:
            for m in r.metrics:
                #setattr(m, '_links', {'self': {'href': {'site_id': site_id, 'id': m.id}}})
                mylinkdata = {}
                for t in ['self','timeseries']:
                    mylinkdata[t] = {'site_id': site_id, 'metric_id': m.id, 'id': m.id}
                setattr(m, '_links', mylinkdata)
        return l
