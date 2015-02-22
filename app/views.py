from app import app, api
from flask import make_response,redirect,url_for
import json

from app.resources import *

@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(json.dumps(data), code)
    #print("output_json.data: {}".format(data['_links']))
    resp.headers.extend(headers or {})
    return resp

api.add_resource(SiteList, '/', '/<string:id>')
api.add_resource(SiteResource, '/sites', '/sites/<string:id>')
api.add_resource(InstrumentResource, '/instruments', '/instruments/<int:id>', '/<string:site_id>/instruments')
api.add_resource(SensorResource, '/sensors', '/sensors/<int:id>')
api.add_resource(CountedMetricResource, 
                 '/metrics', 
                 '/metrics/<int:id>', 
                 '/<string:site_id>/metrics', 
                 '/<string:site_id>/metrics/<int:id>')
# api.add_resource(CountedMetricResource, 
#                  '/cmetrics', 
#                  '/cmetrics/<int:id>', 
#                  '/<string:site_id>/cmetrics', 
#                  '/<string:site_id>/cmetrics/<int:id>')

api.add_resource(UnitResource, '/units', '/units/<int:id>')
api.add_resource(ObservationResource, '/observations', '/observations/<int:id>')
api.add_resource(TimeseriesResource, '/<string:site_id>/timeseries')

#api.add_resource(MetricBySiteResource, '/<string:site_id>/metrics', '/<string:site_id>/metrics/<int:id>')

@app.route('/<string:site_id>/observations')
def post_site_observation(site_id):
    return redirect(url_for('observationresource',site_id=site_id))

@app.errorhandler(404)
def not_found(error):
    return make_response(json.dumps({'error': 'Not found'}), 404)

@app.errorhandler(400)
def not_found(error):
    return make_response(json.dumps({'error': 'Bad request'}), 400)
