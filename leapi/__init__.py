import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.restful import Api
from flask.ext.cors import CORS

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
cors = CORS(app)

db = SQLAlchemy(app)
api = Api(app)

import leapi.views, leapi.models, leapi.resources
