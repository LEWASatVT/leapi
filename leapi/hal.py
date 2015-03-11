import inspect
from itertools import chain
from collections import OrderedDict
from functools import wraps
import json

from flask import make_response
import flask.ext.restplus as restful
from flask.ext.restful.utils import unpack
from flask.views import MethodViewType
from werkzeug.routing import BuildError

def reorder(od):    
    hal = dict(_links=od['_links'])
    if '_embedded' in od:
        hal['_embedded'] = od['_embedded']
    # Reorder OrderedDict so hal objects are first
    return OrderedDict( ( (k, hal.get(k, od.get(k))) for k in chain(hal, od)) )
                

def list_or_nested(v):
    if isinstance(v, list):
        return restful.fields.List(restful.fields.Nested(v[0]))
    elif hasattr(v, '__getitem__'):
        return restful.fields.Nested(v)
    else:
        return restful.fields.Raw(v)
    
def nest_embedded(embedded, model_wrap=lambda x: x):
    edict = dict([ (k, list_or_nested(v)) for k,v in embedded.items()])
    return edict

def upack_helper(v):
    if isinstance(v, tuple):
        return v
    else:
        return (v,v)
    
def link_helper(largs):
    base_args = [ upack_helper(v) for v in largs.items() ]
    return base_args

def key_sub(args, sup_args={}):
    for k,v in sup_args.items():
        if not k == v and k is not None:
            val = args.pop(v, None)
            args[k] = val
    return args

def get_property(resource, name, default=None):
    if hasattr(resource, name):
        return getattr(resource, name, default)
    elif hasattr(resource, 'get'):
        return resource.get(name, default)
    elif hasattr(resource, '__getitem__'):
        try:
            return resource.__getitem__(name)
        except KeyError:
            return default
        #except TypeError as e:
        #    print("TypeError: " + str(e) + " ({})".format(name))
    else:
        print("Don't know what to do with {}".format(type(resource)))
        return None

def set_property(resource, name, value):
    if hasattr(resource, '__setitem__'):
        resource.__setitem__(name, value)
    else:
        try:
            setattr(resource, name, value)
        except AttributeError as e:
            print("AttributeError: " + str(e))
    return resource

def link_args(res, v, default_args={}, target=None):
    if target is not None:
        print("link args for '{}'".format(target))
    sub_args = {}
    args = default_args.copy()
    if hasattr(v, '__iter__'):
        sub_args = v[1]
    #print("args pre sub: {}".format(args))
    #if sub_args:
    #    print("subing args: {}".format(sub_args))
    args = key_sub(args, sub_args)
    largs = dict([ (k, get_property(res, v, 'None')) for k,v in link_helper(args) if v is not None ])
    sub_values = dict([ (k, get_property(res, v, 'None')) for k,v in link_helper(sub_args) if v is not None ])
    largs.update(sub_values)
    return largs
    
def get_class_of_funct(f, *args, **kwargs):
    args_map = {}
    if args or kwargs:
        args_map = inspect.getcallargs(f, *args, **kwargs)
        cls = args_map.pop('self',None)
        if cls is not None:
            cls_name = cls.__class__.__name__
        return cls.__class__, args_map
    else:
        return None, {}
    
class Hal():
    def __init__(self, api, marshal_with=restful.marshal_with, fields=restful.fields):
        self.api = api
        self._marshal_with = marshal_with
        self.fields = fields
        
        @api.representation('application/json+hal')
        def output_json(data, code, headers=None):
            resp = make_response(json.dumps(data), code)
            resp.headers.extend(headers or {})
            return resp

    def marshal_fields(self, fields, embedded, links):
        if embedded:
            fields['_embedded'] = self.fields.Nested(self.api.model('Embedded', nest_embedded(embedded)))

        if '_links' in fields:
            for k,v in links.items():
                fields['_links'][k] = self.api.model(k, {'href': restful.fields.Url(v[0])})
        return fields
    
    def marshal_with(self, fields, **kwargs):
        '''
        A decorator that modifies fields and data to add HAL specific fields

        :param embedded: provide a list of resources that will be embedded in this response
        :param links: provide a list of links that will be appended to this response
        '''

        #def __init__(self, hal, fields, **kwargs):
        embedded = kwargs.pop('embedded', {})
        links = kwargs.pop('links', {})
            
        fields = self.marshal_fields(fields, embedded, links)
        cls_name = "Unknown Class"
                
        def hal_wrapped(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                cls, args_map = get_class_of_funct(f, *args, **kwargs)

                if cls is not None:
                    cls_name = cls.__name__
                    
                if hasattr(cls, '_nested_links'):
                    nested_links = cls._nested_links
                    for k,v in nested_links.items():
                        v.nested = self.api.model(k, v.nested)
                    cls.fields['_links'] = restful.fields.Nested(self.api.model('Links',nested_links))

                link_args = dict([ (k,k) for k in args_map.keys() ])
                if 'self' not in links:
                    links['self'] = (cls_name, link_args)

                resp = f(*args, **kwargs)
                if isinstance(resp, tuple):
                    data, code, headers = unpack(resp)
                    if embedded:
                        apply_to_possible_list(data, set_embedded(embedded))
                    if links:
                        apply_to_possible_list(data, set_links(links, link_args))
                    return (data, code, headers)
                else:
                    if embedded:
                        apply_to_possible_list(resp, set_embedded(embedded))
                    if links:
                        apply_to_possible_list(resp, set_links(links, link_args))
                    return resp
            return wrapper
        
        def wrapper(f):
            return self._marshal_with(fields, **kwargs)(hal_wrapped(f))
        return wrapper
        #return hal_decorator
                             
# Utils for merge_hal
def resource_or_all(data, emb):
    attr = get_property(data, emb)
    if hasattr(attr, 'all'):
        return attr.all()
    else:
        return attr

def apply_to_possible_list(data, f):
    if isinstance(data, list):
        for d in data:
            f(d)
    else:
        f(data)
    return data

def make_embedded(data, embedded):
    return dict([ (emb, resource_or_all(data, emb)) for emb,res in embedded.items() ])

def set_embedded(embedded):
    return lambda r: set_property(r, '_embedded', make_embedded(r, embedded))

def make_links(res, links, default_args={}):
    link_data = {}
    if hasattr(links,'items'):
        link_data = dict([ (t, link_args(res, v, default_args)) for t,v in links.items() ])
    return link_data

def set_links(links, sup_args={}):
    return lambda r: set_property(r, '_links',  make_links(r, links, sup_args))

class HalResourceType(MethodViewType):
    def __new__(cls, name, bases, attrs):
        if name.startswith('None'):
            return None
            
        newattrs = {}
        #attrs['get'] = halify(api)(attrs['get'])
        #for attrname, attrvalue in attr.iteritems():
        #attrs['_link_args'] = ['id'] + ([] if 'link_args' not in attrs else attrs['link_args'])
        if 'fields' in attrs:
            links = {'self': restful.fields.Nested({'href': restful.fields.Url(name.lower()) }) }
            if '_links' in attrs:
                for t,v in attrs['_links'].items():
                    links[t] = restful.fields.Nested({'href': restful.fields.Url(v[0].lower())})
            attrs['_nested_links'] = links
            #attrs['fields']['_links'] = restful.fields.Nested(links)
            #if '_embedded' in attrs:
            #    attrs['fields']['_embedded'] = restful.fields.Nested(nest_embedded(attrs['_embedded']))

        return super(HalResourceType, cls).__new__(cls, name, bases, attrs)

    def __init__(self, name, bases, attrs):
        super(HalResourceType, self).__init__(name, bases, attrs)

class Resource(restful.Resource):
    __metaclass__ = HalResourceType
    def get(self):
        pass

