from flask.ext.restful import Resource
from flask.ext.restful import marshal_with
from flask.ext.restful import fields as restful_fields
from flask.views import MethodViewType
from itertools import chain

from collections import OrderedDict

from app import api
from functools import wraps

## not currently used
def makeLink():
    registry = {}
    def registrar(func):
        def wrapper(*args):
            return { "href": func(*args) }
        registry[func.__name__] = wrapper
        return wrapper

    registrar.all = registry
    return registrar

## not currently used
class HalView(object):
    link = makeLink()

    def _links(self):
        l = dict([ (rel,href(self)) for rel,href in HalView.link.all.items() ])
        try:
            l['curies'] = self.curies()
        except AttributeError:
            pass
        return l

class marshal_with(marshal_with):
    ## TODO may need to override restful.marshal to get _embedded in there properly
    def __init__(self, fields, envelope=None):
        fields['_links'] = restful_fields.Raw
        super(marshal_with, self).__init__(fields, envelope)

def make_self(uri, d):
    print("d: {}".format(d))
    if 'id' in d:
        uri = uri + "/{}".format(d['id'])
    return { 'self': { 'href': uri } }

def reorder(od):    
    hal = dict(_links=od['_links'])
    if '_embedded' in od:
        hal['_embedded'] = od['_embedded']
    # Reorder OrderedDict so hal objects are first
    return OrderedDict( ( (k, hal.get(k, od.get(k))) for k in chain(hal, od)) )

def _halify(data, api, uri):
    # TODO when would this list ever have more than a single item?
    if isinstance(data, (list, tuple)):
        for d in data:
            d['_links'] = make_self(uri, d)
            d = reorder(d)
    else:
        data['_links'] = make_self(uri, data)
        data = reorder(data)
    return data

class halify(object):
    def __init__(self, api):
        self.api = api

    def __call__(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            resource = args[0]
            print("halify: ({}, {})".format(resource, kwargs))
            self_uri = self.api.url_for(resource)
            resp = f(*args, **kwargs)
            if isinstance(resp, tuple):
                data, code, headers = unpack(resp)
                return _halify(data, self.api, self_uri), code, headers
            else:
                return _halify(resp, self.api, self_uri)
        return wrapper
                
class HalResourceType(MethodViewType):
    def __new__(cls, name, bases, attrs):
        if name.startswith('None'):
            return None
            
        newattrs = {}
        attrs['get'] = halify(api)(attrs['get'])
        #for attrname, attrvalue in attr.iteritems():
        if '_embedded' in attrs:
            print("HalResourceType attrs: {}".format(attrs['_embedded']))
        return super(HalResourceType, cls).__new__(cls, name, bases, attrs)

    def __init__(self, name, bases, attrs):
        super(HalResourceType, self).__init__(name, bases, attrs)

class HalResource(Resource):
    __metaclass__ = HalResourceType
    def get(self):
        pass

