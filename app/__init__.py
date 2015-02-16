import os
from flask import Flask
from flask.ext.cors import CORS
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.restful import Api

app = Flask(__name__)
cors = CORS(app)
app.config.from_object(os.environ['APP_SETTINGS'])
db = SQLAlchemy(app)
api = Api(app)

from app import views,models,resources
