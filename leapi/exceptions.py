import logging
import re
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

class StorageIntegrityError(InvalidUsage):
    def __init__(self, payload=None):
        InvalidUsage.__init__(self, 'Integerity Error', 409)
        m = re.search(r'duplicate key value violates unique constraint "([^"]+)"', payload)
        if m:
            dm = re.search(r'DETAIL:\s+(.*)', payload)
            self.payload = [ ('reason', 'unique constraint violation'), 
                             ('key', m.group(1)), 
                             ('detail', dm.group(1)) 
            ]
        else:
            self.payload = [ ('reason', payload) ]

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    logging.info(str({'status': error.status_code, 'response': error.to_dict()}))
    return response
