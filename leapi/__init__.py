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


import leapi.views, leapi.models, leapi.resources
import leapi.archive
