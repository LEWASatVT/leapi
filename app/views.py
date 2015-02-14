from app import app, models
from flask.ext.restful import Api
from flask import make_response
import json

api = Api(app)

from app.resources import SiteResource, InstrumentResource, SensorResource, VariableResource, ObservationResource

@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(json.dumps(data), code)
    resp.headers.extend(headers or {})
    return resp

api.add_resource(SiteResource, '/sites', '/sites/<string:id>')
api.add_resource(InstrumentResource, '/instruments', '/instruments/<int:id>')
api.add_resource(SensorResource, '/sensors', '/sensors/<int:id>')
api.add_resource(VariableResource, '/variables', '/variables/<int:id>')
api.add_resource(ObservationResource, '/observations', '/observations/<int:id>')

@app.errorhandler(404)
def not_found(error):
    return make_response(json.dumps({'error': 'Not found'}), 404)

@app.errorhandler(400)
def not_found(error):
    return make_response(json.dumps({'error': 'Bad request'}), 400)
