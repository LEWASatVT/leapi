import inspect
from itertools import chain
from collections import OrderedDict
from functools import wraps
import json
import logging

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
                

def list_or_nested(v,k):
    fields = restful.fields.Raw(v)
    if isinstance(v, list):
        for res in v:
            res['_links'] = restful.fields.Nested(self_link(res))

        fields = restful.fields.List(restful.fields.Nested(v[0]))
    elif hasattr(v, '__getitem__'):
        logging.debug("setting self link for {}".format(k))
        v['_links'] = restful.fields.Nested(self_link(k + 'resource'))
        fields = restful.fields.Nested(v)
    return fields
    
def nest_embedded(embedded, model_wrap=lambda x: x):
    edict = dict([ (k, list_or_nested(v,k)) for k,v in embedded.items()])
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
        logging.debug("Attempt to get unknown property {} on {}".format(name, type(resource)))
        return None

def set_property(resource, name, value):
    if hasattr(resource, '__setitem__'):
        resource.__setitem__(name, value)
    else:
        try:
            setattr(resource, name, value)
        except AttributeError as e:
            logging.error("AttributeError: " + str(e))
    return resource
    
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
    def __init__(self, api, marshal_with=restful.marshal_with, fields=restful.fields, **kwargs):
        self.api = api
        self._marshal_with = marshal_with
        self.fields = fields
        self.debug = kwargs.get('debug', False)
        
        @api.representation('application/json+hal')
        def output_json(data, code, headers=None):
            data = json.dumps(data, indent=4) + "\n" if self.debug else json.dumps(data)
            resp = make_response(data, code)
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
                        logging.debug("setting _embedded on {}".format(resp))
                        apply_to_possible_list(resp, set_embedded(embedded))
                    if links:
                        logging.debug("setting links on resp with _embedded = {}".format(get_property(resp,'_embedded',None)))
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

def link_args(res, v, default_args={}, target=None):
    """
    :res the resource name
    :v resource name or tuple with resource name and list of name substitutions
    """
    if target is not None:
        logging.debug("link args for '{}'".format(target))
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

def make_links(res, links, default_args={}, embedded=None):
    link_data = {}
    if hasattr(links,'items'):
        link_data = dict([ (t, link_args(res, v, default_args)) for t,v in links.items() ])
    ## TODO figure out how to populat embedded links arguments
    # ultimately data ~ {'_embedded': {'instruments': [ {'_links': {'self': link_args}}, ... ] } }
    return link_data

def set_links(links, sup_args={}):
    def _set_links(res):
        logging.debug("_set_links: links is {}".format(links))
        set_property(res, '_links', make_links(res, links, sup_args))
        embedded = get_property(res, '_embedded')
        if hasattr(embedded, 'items'):
            for k,e in embedded.items():
                #set_property(e, '_links', {'self': sup_args})
                link_data = HalResourceType.link_data.get(k+'resource', {})
                logging.debug("sup_args: {}".format(sup_args))
                self_data = sup_args
                self_data.pop(k + '_id',None)
                self_data['id'] = 'id'
                link_data['self'] = ('SelfResource', self_data)
                logging.debug("setting embedded links on {},{} with {}".format(k,e,link_data))
                set_property(e, '_links', make_links(e, link_data, sup_args))
                
    return _set_links

def self_link(res_name):
    return {'self': restful.fields.Nested({'href': restful.fields.Url(res_name) }) }

class HalResourceType(MethodViewType):
    
    link_data = {}

    def __new__(cls, name, bases, attrs):
        if name.startswith('None'):
            return None
            
        newattrs = {}
        #attrs['get'] = halify(api)(attrs['get'])
        #for attrname, attrvalue in attr.iteritems():
        #attrs['_link_args'] = ['id'] + ([] if 'link_args' not in attrs else attrs['link_args'])
        if 'fields' in attrs:
            links = self_link(name.lower())

            if '_links' in attrs:
                HalResourceType.link_data[name.lower()] = attrs['_links']
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

