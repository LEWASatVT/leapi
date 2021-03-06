from leapi import app, api
from flask import g,make_response,redirect,url_for
import json

from leapi.resources import *

#@api.representation('application/json')
#def output_json(data, code, headers=None):
#    resp = make_response(json.dumps(data), code)
    #print("output_json.data: {}".format(data['_links']))
#    resp.headers.extend(headers or {})
#    return resp

api.add_resource(SiteList, '/')
api.add_resource(SiteResource, '/sites', '/sites/<string:id>')
api.add_resource(InstrumentResource, 
                 '/sites/<string:site_id>/instruments',
                 '/sites/<string:site_id>/instruments/<string:name>')
api.add_resource(SensorResource, 
                 '/sites/<string:site_id>/instruments/<string:instrument_name>/sensors', 
                 '/sites/<string:site_id>/instruments/<string:instrument_name>/sensors/<int:id>')

api.add_resource(CountedMetricResource, '/sites/<string:site_id>/metrics/<int:id>', endpoint='metricresource')
api.add_resource(CountedMetricList, '/sites/<string:site_id>/metrics', endpoint='metricresourcelist')

api.add_resource(UnitResource, '/units', '/units/<int:id>')

api.add_resource(ObservationList, 
                 '/sites/<string:site_id>/observations',
                 '/sites/<string:site_id>/instruments/<string:instrument_name>/observations')

api.add_resource(ObservationResource, 
                 '/sites/<string:site_id>/observations/<int:id>',
                 '/sites/<string:site_id>/instruments/<string:instrument_name>/observations/<int:id>',
)

api.add_resource(TimeseriesResource, 
                 '/sites/<string:site_id>/metrics/<int:metric_id>/timeseries',
)

api.add_resource(MetricGroupList,
                 '/sites/<string:site_id>/metricgroups'
                 )

api.add_resource(MetricGroup,
                 '/sites/<string:site_id>/metricgroups/<string:name>'
                 )

api.add_resource(FlagList,
                 '/sites/<string:site_id>/flags')

api.add_resource(MediaListResource,
                 '/media'
                 )

api.add_resource(MediaResource,
                 '/media/<int:id>'
                 )

api.add_resource(MediaContentResource,
                 '/media/<int:id>/content'
                 )

@app.errorhandler(404)
def not_found(error):
    return make_response(json.dumps({'error': 'Not found'}), 404)

@app.errorhandler(400)
def not_found(error):
    return make_response(json.dumps({'error': 'Bad request'}), 400)

    
