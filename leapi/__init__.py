import os
from flask import Flask, Blueprint
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.restplus import Api, apidoc
from flask.ext.cors import CORS

from leapi.hal import Hal

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
cors = CORS(app)

db = SQLAlchemy(app)
api = Api(app, version='0.9', title='LeAPI',
          description='A multi-site environmental monitoring API developed at and for the <a href="http://www.lewas.centers.vt.edu">LEWAS Lab</a>',
          contact='dmaczka@vt.edu', ui=False, default='leapi')
        
hal = Hal(api, marshal_with=api.marshal_with, debug=app.debug)

import leapi.views, leapi.models, leapi.resources
import leapi.archive
import util 
import swagger


