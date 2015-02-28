from leapi import app, api
from flask import make_response,redirect,url_for
import json

from leapi.resources import *

@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(json.dumps(data), code)
    #print("output_json.data: {}".format(data['_links']))
    resp.headers.extend(headers or {})
    return resp

print("loading views")
api.add_resource(SiteList, '/')
api.add_resource(SiteResource, '/sites', '/sites/<string:id>')
api.add_resource(InstrumentResource, 
                 '/sites/<string:site_id>/instruments',
                 '/sites/<string:site_id>/instruments/<int:id>')
api.add_resource(SensorResource, 
                 '/sites/<string:site_id>/instruments/<string:instrument_name>/sensors', 
                 '/sites/<string:site_id>/instruments/<string:instrument_name>/sensors/<int:id>')
api.add_resource(CountedMetricResource, 
                 '/sites/<string:site_id>/metrics', 
                 '/sites/<string:site_id>/metrics/<int:id>')

api.add_resource(UnitResource, '/units', '/units/<int:id>')
api.add_resource(ObservationResource, 
                 '/sites/<string:site_id>/instruments/<int:instrument_id>/observations',
                 '/sites/<string:site_id>/instruments/<string:instrument_name>/observations',
)

api.add_resource(TimeseriesResource, 
                 '/sites/<string:site_id>/metrics/<int:metric_id>/timeseries',
)

@app.errorhandler(404)
def not_found(error):
    return make_response(json.dumps({'error': 'Not found'}), 404)

@app.errorhandler(400)
def not_found(error):
    return make_response(json.dumps({'error': 'Bad request'}), 400)
