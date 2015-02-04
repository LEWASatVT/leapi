from app import app, models
from schematics.models import Model
from schematics.types import FloatType,DateTimeType,IntType,StringType
from flask_halalchemy import FormView,IndexView,ResourceView
from flask import request, jsonify, make_response, abort

def hal_alchemy_encoder(embed = []):
    class HalAlchemyEncoder(json.JSONEncoder):
        def default(self,obj):
            if isinstance(obj.__class__, DeclarativeMeta):
                fields = {}
                for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                    val = obj.__getattribute__(field)

                    # is this field another SQLAlchemy object?
                    
class ObservationResource(ResourceView):
    def query(self):
        ob = models.Observation.query.get_or_404(self.url_kwargs['id'])
        return ob
    
class ObservationIndex(IndexView):
    per_page = 10

    def query(self):
        return models.Observation.query.order_by(models.Observation.datetime)

import sys

class ObservationModel(Model):
    value = FloatType(required=True)
    datetime = DateTimeType(required=True)
    
class ObservationForm(FormView):
    
    fields = {
        "value": FloatType(required=True),
        "datetime": DateTimeType(required=True)
        #"variable": StringType(required=True),
        #"unit": StringType(required=True)
    }

    def post(self):
        #sys.stderr.write("self.clean: {}\n".format(self.clean))
        observation = Observation(**self.clean)
        #observation.unit = models.Unit.query.get(self.clean.unit['id'])
        #observation.variable = models.Variable.query.get(self.clean.variable['id'])
        db.session.add(observation)
        resource = ObservationResource.as_resource('observation', observation)
        response = make_response(resource.get())
        return (response, 201, {'Location': resource.url})

class VariableResource(ResourceView):
    def query(self):
        return models.Variable.query.get_or_404(self.url_kwargs['id'])
    
class VariableIndex(IndexView):
    per_page = 10
    
    def query(self):
        return models.Variable.query.all()

@app.route('/index')
def index():
    return "Hello World 2!"

#@app.route('/variables')
#def variables():
#    vs = models.Observation.query.all()
    
observation_resource = ObservationResource.as_view('observation')
observation_index = ObservationIndex.as_view('observations', subresource_endpoint='observation')
observation_form = ObservationForm.as_view('observation_form')

app.add_url_rule('/variables', view_func=VariableIndex.as_view('variables', subresource_endpoint='variable'), methods=['GET'])
app.add_url_rule('/observations/<int:id>', view_func=observation_resource, methods=['GET'])
app.add_url_rule('/observations', view_func=observation_index, methods=['GET'])
app.add_url_rule('/observations', view_func=observation_form, methods=['POST', 'OPTIONS'])

@app.route('/observations2', methods=['POST', 'OPTIONS'])
def add_observation():
    if not request.json:
        abort(400)
    data = request.json
    sys.stderr.write("form data: {}\n".format(data))
    return jsonify({'message': 'working'}), 201

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)
