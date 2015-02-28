import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.restful import Api

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.debug = False
db = SQLAlchemy(app)
api = Api(app)

#from leapi.resources import *

#api.add_resource(SiteList, '/')

import leapi.views, leapi.models, leapi.resources
