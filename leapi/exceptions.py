import logging
from flask import jsonify
from leapi import app

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = {}
        try:
            rv = dict(self.payload or ())
        except ValueError, e:
            logging.error("{}: payload: {}".format(e, self.payload))
        finally:
            rv['message'] = self.message
            return rv

class AuthFailure(InvalidUsage):
    def __init__(self, payload=None):
        InvalidUsage.__init__(self, 'Authentication Failed',403)
        self.payload = [ ('debug', payload ) ]


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response
