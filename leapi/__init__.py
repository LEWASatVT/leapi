import os
from flask import Flask, Blueprint
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.restplus import Api, apidoc
from flask.ext.cors import CORS

from leapi.hal import Hal

app = Flask(__name__)
#blueprint = Blueprint('api', __name__, url_prefix='/api')
app.config.from_object(os.environ['APP_SETTINGS'])
cors = CORS(app)

db = SQLAlchemy(app)
api = Api(app, version='0.9', title='LeAPI',
          description='A multi-site environmental monitoring API developed at and for the <a href="http://www.lewas.centers.vt.edu">LEWAS Lab</a>',
          contact='dmaczka@vt.edu', ui=False, default='leapi')
        
hal = Hal(api, marshal_with=api.marshal_with)

#ns = api.namespace('leapi', description='TODO operations')

import leapi.views, leapi.models, leapi.resources
import leapi.archive

if not app.debug:
    import logging
    from logging import handlers
    file_handler = handlers.RotatingFileHandler('/var/log/flask/leapi.log')
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)

    from logging import Formatter
    file_handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))


@app.route('/leapi-doc/', endpoint='doc')
def swagger_ui():
        return apidoc.ui_for(api)
    
#app.register_blueprint(blueprint)
#app.register_blueprint(apidoc)

if app.debug:
    @app.route('/swaggerui/bower/<string:path>')
    def send_bower(path):
        return send_from_directory('bower_components', path)

