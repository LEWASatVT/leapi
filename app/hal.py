from flask.ext.restful import Resource
from flask.ext.restful import marshal_with,marshal
from flask.ext.restful import fields as restful_fields
from flask.views import MethodViewType
from itertools import chain
from werkzeug.routing import BuildError

from collections import OrderedDict

from app import api
from functools import wraps
import resources

class Embedded(restful_fields.Raw):
    def __init__(self, cls):
        self.cls = cls

    def output(self, key, obj):
        if obj is None:
            return None
        if hasattr(self.cls, 'fields'):
            #print ("embedding {},{} with fields {}".format(key,obj.keys(), self.cls.fields))
            if hasattr(obj, '__getitem__'):
                try:
                    return marshal(obj[key], self.cls.fields)
                except KeyError,e:
                    print("KeyError on {} ({})".format(obj,str(e)))
            return marshal(obj, self.cls.fields)
        
    def __repr__(self):
        return "Embedded({})".format(self.cls.__name__)
    #def output(self, key, obj):
    #    print("{}: {}".format(key,obj[key]))
    #    if hasattr(self.cls, 'fields'):
    #        return marshal(obj[key], self.cls.fields)
    #    return marshal(obj, {})

class marshal_with(marshal_with):
    ## TODO may need to override restful.marshal to get _embedded in there properly
    def __init__(self, fields, envelope=None):
        fields['_links'] = restful_fields.Raw
        super(marshal_with, self).__init__(fields)

def make_self(uri):
    return { 'self': { 'href': uri } }

def reorder(od):    
    hal = dict(_links=od['_links'])
    if '_embedded' in od:
        hal['_embedded'] = od['_embedded']
    # Reorder OrderedDict so hal objects are first
    return OrderedDict( ( (k, hal.get(k, od.get(k))) for k in chain(hal, od)) )

## No longer used, may remove at some point if not needed for reference
# def _halify(data, api, uri):
#     # TODO when would this list ever have more than a single item?
#     if isinstance(data, (list, tuple)):
#         for d in data:
#             try:
#                 d['_links'] = make_self(uri)
#                 d = reorder(d)
#             except TypeError, e:
#                 pass #print("TypeError d: {}".format(data))

#     else:
#         data['_links'] = make_self(uri)
#         data = reorder(data)
#     return data

## Referece for adding a decorator to methods
# class halify(object):
#     def __init__(self, api):
#         self.api = api

#     def __call__(self, f):
#         @wraps(f)
#         def wrapper(*args, **kwargs):
#             resource = args[0]
#             print("halify: ({}, {})".format(resource.endpoint, kwargs))
#             #self_uri = self.api.url_for(resource)
#             try:
#                 self_uri = self.api.url_for(resource, **kwargs)
#             except BuildError,e:
#                 self_uri = '/build_error'
#             resp = f(*args, **kwargs)
#             if isinstance(resp, tuple):
#                 data, code, headers = unpack(resp)
#                 return _halify(data, self.api, self_uri), code, headers
#             else:
#                 return _halify(resp, self.api, self_uri)
#         return wrapper
                
def resourceName(field_name):
    return field_name.capitalize() + 'Resource'

def getResource(field):
    #print("getting resource for {}".format(field))
    if isinstance(field, tuple):
        resource_name = field[1]
    else:
        resource_name = field
    try:
        return getattr(resources,resource_name)
    except AttributeError,e:
        return None

def resourcePair(field):
    field_name = field[0] if isinstance(field, tuple) else field
    resource_name = field[1] if isinstance(field, tuple) else resourceName(field)
    obj = getResource(resource_name)
    #print("obj for {} is {}".format(field,obj))
    if obj:
        return (field_name, Embedded(obj))
    return (field_name, restful_fields.Raw)

class HalLink(restful_fields.Raw):
    def __init__(self,name, args):
        self.rname = name
        self.args = args
        self.attribute = 'get'

    def output(self, key, obj):
        if obj is None:
            return ""
        res = getResource(self.rname)
        #print("getting HalLink for {} with ({},{}) of type {}".format(res,key,obj,type(obj)))
        if hasattr(obj, '__dict__'):
            obj = obj.__dict__
        obj = dict([ (k,v) for k,v in obj.items() if k in self.args ])
        if res:
            try:
                return { 'href': api.url_for(res, **obj) }
            except BuildError,e:
                return { 'builderror': str(e) }
        return '/'

class HalResourceType(MethodViewType):
    def __new__(cls, name, bases, attrs):
        if name.startswith('None'):
            return None
            
        newattrs = {}
        #attrs['get'] = halify(api)(attrs['get'])
        #for attrname, attrvalue in attr.iteritems():
        attrs['_link_args'] = ['id'] + ([] if 'link_args' not in attrs else attrs['link_args'])
        if 'fields' in attrs:
            attrs['fields']['_links'] = { 'self': HalLink(name, attrs['_link_args']) }

        if '_embedded' in attrs:
            if hasattr(attrs['_embedded'], 'items'):
                #print("building embedded dict from dict")
                attrs['fields']['_embedded'] = dict([ (key, Embedded(obj)) for key,obj in attrs['_embedded'].items() ])
            elif hasattr(attrs['_embedded'], '__iter__'):
                #print("{}: building embedded dict from itterable".format(name))                
                edict = dict([ resourcePair(f) for f in attrs['_embedded'] ])
                edict = dict( [ (k,v) for k,v in edict.items() if isinstance(v, Embedded) ] )
                #print("{}: edict: {}".format(name, edict))
                attrs['fields']['_embedded'] = edict

        if '_links' in attrs:
            for t,l in attrs['_links'].items():
                attrs['fields']['_links'][t] = l

        return super(HalResourceType, cls).__new__(cls, name, bases, attrs)

    def __init__(self, name, bases, attrs):
        super(HalResourceType, self).__init__(name, bases, attrs)

class HalResource(Resource):
    __metaclass__ = HalResourceType
    def get(self):
        pass
