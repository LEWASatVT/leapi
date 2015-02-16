from app import app, api, models
from flask import make_response
import json


from app.resources import SiteResource, SiteList, InstrumentResource, SensorResource, MetricResource, ObservationResource, UnitResource, TimeseriesResource

@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(json.dumps(data), code)
    #print("output_json.data: {}".format(data['_links']))
    resp.headers.extend(headers or {})
    return resp

api.add_resource(SiteList, '/')
api.add_resource(SiteResource, '/sites', '/sites/<string:id>')
api.add_resource(InstrumentResource, '/instruments', '/instruments/<int:id>')
api.add_resource(SensorResource, '/sensors', '/sensors/<int:id>')
api.add_resource(MetricResource, '/metrics', '/metrics/<int:id>')
api.add_resource(UnitResource, '/units', '/units/<int:id>')
api.add_resource(ObservationResource, '/observations', '/observations/<int:id>')
api.add_resource(TimeseriesResource, '/<string:site_id>/timeseries')

@app.route('/<string:site_id>/observations')
def post_site_observation(site_id):
    pass

@app.errorhandler(404)
def not_found(error):
    return make_response(json.dumps({'error': 'Not found'}), 404)

@app.errorhandler(400)
def not_found(error):
    return make_response(json.dumps({'error': 'Bad request'}), 400)
