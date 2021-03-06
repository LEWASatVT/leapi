from flask import request
import logging
from datetime import timedelta

from sqlalchemy.exc import IntegrityError,DataError
from sqlalchemy.orm.exc import FlushError

from flask.ext.restplus import fields
from flask.ext.restful import abort, inputs

from leapi.hal import Resource
from leapi import db, app, api, hal
from leapi.models import Observation,Site,Sensor,Metric,CountedMetric,Unit,Instrument,OffsetType,Flag
from leapi.resources import metric, unit, instrument, sensor
from leapi.exceptions import AuthFailure, InvalidUsage, StorageIntegrityError
            
def by_id_or_filter(obj, args, atname=None):
    '''find object by id if supplied, and if not construct filter from args'''
    atname = obj.__name__.lower() if atname == None else atname

    if atname == 'countedmetric':
        print("finding countedmetric by {}".format(args[atname]))    

    res = None
    if atname not in args or not args[atname]:
        return None

    if 'id' in args[atname]:
        res = obj.query.get(args[atname]['id'])
    else:
        res = obj.query.filter_by(**dict(args[atname].items())).first()
    return res

parser = api.parser()
parser.add_argument('value', type=float, required=True, help="value observed", location='json')
parser.add_argument('datetime', type=inputs.datetime_from_rfc822, required=True, help="date and time observation was made", location='json')
parser.add_argument('units', type=dict, required=True, help="units observation value is in", location='json')
parser.add_argument('metric', type=dict, required=True, help="metric the observation observed", location='json')
parser.add_argument('instrument', type=dict, help="instrument that made the observation")
parser.add_argument('site', type=dict, help="missing site_id", location='json')
parser.add_argument('sensor', type=dict) #TODO once established, make required 
parser.add_argument('offset', type=dict, help="physical or temporal offset of observed value", location='json')
parser.add_argument('stderr', type=float, help="standard deviation of observed value", location='json')
parser.add_argument('magicsecret', default='magicsecret', type=str)

fetch_parser = api.parser()
fetch_parser.add_argument('metric.name', type=str, location='args')
fetch_parser.add_argument('metric.medium', type=str, location='args')
fetch_parser.add_argument('limit', type=int, default=100, location='args')

#parser = api.parser()
#parser.add_argument('body', type=dict, required=True, help="Body of request", location="json")

offset_model = api.model('offset',
                         {'value': fields.Float(),
                          'type_id': fields.Integer(),
                          'type': fields.String()
                      })

observation_model = api.model('BaseObservation',
                              {
                                  'datetime': fields.DateTime(required=True, description='A formated datetime string'),
                                  'value': fields.Float(required=True),
                                  'offset_value': fields.Float(),
                                  'offset_type_id': fields.Integer(),
                                  'offset': fields.Nested(offset_model), 
                                  'stderr': fields.Float(description='Standard error associated with value'),
                                  'site_id': fields.String(required=True),
                                  'method_id': fields.Integer(default=1),
                                  'flags': fields.List(fields.String())
                              })

                            # TODO: When we get materialized views working on server we can use CountedMetricResource
_embedded = api.model('observation_embedded',
                     { 'metric': metric.MetricResource.fields,
                       'units': unit.UnitResource.fields,
                       'instrument': instrument.InstrumentResource.fields,
                   })

get_fields = api.extend('Observation', observation_model, 
                        {
                            'id': fields.Integer(),
                            '_embedded': fields.Nested(_embedded)
                        })

post_fields = api.extend('ObservationPost', observation_model,
                         {
                             'metric': fields.Nested(metric.MetricResource.fields),
                             'units': fields.Nested(unit.UnitResource.fields),
                             'instrument': fields.Nested(instrument.InstrumentResource.fields),
                             'magicsecret': fields.String()
                         })

observation_response = api.model('ObservationResponse',
                                {
                                    'status': fields.Integer(),
                                    'response': fields.Nested(get_fields),
                                    'messages': fields.List(fields.String())
                                })                           

def parse_with_model(doc, model):
    args = {}
    for key in model:
        args[key] = doc.get(key, None)
    return args
        
def prep_observation(odoc, site_id, instrument_name):
    '''Construct a single observation object'''
    args = {}
    messages = []
    if hasattr(odoc, 'unparsed_arguments'):
        args = parser.parse_args(odoc)
    else:
        args = parse_with_model(odoc, post_fields)

    r = None

    auth = False
    auth_messages = []
    if 'CLIENT_VERIFY' in request.environ:
        # use SSL auth
        if request.environ['CLIENT_VERIFY'] == "SUCCESS":
            #http://stackoverflow.com/a/23654676
            cert = request.environ['CLIENT_CERT'].split("/")[1:]
            cert = {p[0]: p[1] for p in [a.split("=") for a in cert]}
            if cert["CN"].split(".")[0] == site_id:
                auth = True
            else:
                auth_messages.append('CN does not match site_id');
        else:
            auth_messages.append('CLIENT_VERIFY != "SUCCESS"');
    else:
        auth_messages.append('CLIENT_VERIFY not in request.environ')

    if not auth and app.config.get('PASSWORD_FALLBACK', True):
        auth_messages.append('fallback to password auth')
        #Fall back to password auth
        if ('MAGICSECRET' in app.config) and (args['magicsecret'] == app.config['MAGICSECRET']):
            auth = True
        else:
            logging.debug('magicsecret fail: {} != {}'.format(args['magicsecret'],app.config['MAGICSECRET']))
    if not auth:
        return (r, 403, auth_messages)

    # TODO: When materialize views are implemented we can use CountedMetric
    metric = by_id_or_filter(Metric, args, 'metric')
    unit = Unit.query.filter_by(abbv=args['units']['abbv']).first()
    #sensor = by_id_or_filter(Sensor, args)

    if unit == None:
        messages.append("No unit with abbv: {}".format(args['units']['abbv']))
    if metric == None:
        messages.append("No metric with: {}".format(args['metric']))
    if len(messages) > 0:
        logging.warn("errors: {}".format(messages))
        return (r, 400, messages)

    r = Observation(datetime=args['datetime'], value=args['value'], site_id=site_id)

    r.site_id = site_id
    r.instrument_name = instrument_name
    r.metric = metric
    r.metric_id = metric.id
    r.units = unit
    r.stderr = args['stderr']
    r.method_id = args['method_id']
    
    if args['offset']:
        offset = OffsetType.query.filter_by(description=args['offset']['type']).first()
        r.offset_value = args['offset']['value']
        r.offset_type_id = offset.id
    else:
        r.offset_value = 0;
        r.offset_type_id = OffsetType.query.filter_by(description='none').first().id

    if args['flags']:
        for flag in args.get('flags', []):
            flags = Flag.query.filter(Flag.name.in_(args['flags'])).all()
            r.flags = flags
        
    return (r, 201, messages)

    #@api.doc(params={'site_id': 'A site ID', 'instrument_id': 'An instrument ID'})
class ObservationResource(Resource):
    '''Show a single observation made or post a new one. Primary resource used by sensor layer'''

    #fields=get_fields
    
    _embedded = { 'metric': metric.MetricResource.fields,
                  'units': unit.UnitResource.fields,
                  'instrument': instrument.InstrumentResource.fields
              }

    @hal.marshal_with(get_fields, embedded=_embedded)
    @api.doc(description="Not particularly useful for timeseries analysis, that's what the timeseries resource is for")
    def get(self, site_id, id, instrument_name=None):
        '''get a particular observation or list of observations. Not terribly useful, you probably want timeseries'''
        filters = []
        if instrument_name is not None:
            filters.append(Instrument.name==instrument_name)
        if site_id is not None:
            filters.append(Site.id==site_id)
        
        if len(filters) > 0:
            filters.append(Observation.id==id)
            r = Observation.query.join(Site).filter(*filters).first()
            if not r:
                abort(404)
        else:
            r = Observation.query.get_or_404(id)
        setattr(r,'_embedded', {'metric': r.metric })
        return r

class ObservationList(Resource):
    #fields=get_fields
    
    @hal.marshal_with(get_fields, embedded=_embedded, as_list=True)
    @api.doc(parser=fetch_parser)
    def get(self, site_id, instrument_name=None):
        args = fetch_parser.parse_args()

        filterexp = [Site.id==site_id,
                     Observation.site_id==site_id,
                     Observation.metric_id==Metric.id,
                     Observation.instrument_name==Instrument.name]
        if instrument_name:
            filterexp.append(Observation.instrument_name==instrument_name)
        if args['metric.name']:
            filterexp.append(Metric.name==args['metric.name'])
        if args['metric.medium']:
            filterexp.append(Metric.medium==args['metric.medium'])
        
        q = Observation.query.join(Site,Instrument,Metric).\
                             filter(*filterexp).\
                             order_by(Observation.datetime.desc(),Observation.metric_id,Observation.offset_value).\
                             limit(args['limit'])
        result = q.all()

        return result
        
    @api.marshal_list_with(observation_response, code=201)
    @api.expect(post_fields)
    @api.doc(responses={201: 'Observation created'}, description="Only enough fields in the embedded resources units,metric and instrument need be provided to identify an existing record")
    def post(self, site_id, instrument_name):
        '''Post a new observation'''
        if not request.json:
            print("request was not JSON")
            api.abort(400, message="request must be JSON")
        errors = []
        codes = []
        
        if isinstance(request.json, list):
            codes = [ prep_observation(o, site_id, instrument_name) for o in request.json]
        else:
            codes = [ prep_observation(request.json, site_id, instrument_name) ]

        for (r,code,errors) in codes:
            if code == 201: #TODO: is there a return code for "partial success"?
                db.session.add(r)

        #TODO: On some of these errors, IntegrityError in particular, it may make sense
        #to go back and try each observation as a separate commit to find the one that caused the error
        #then update the returned status
        try:
            db.session.commit()
        except DataError, e:
            api.abort(400, message=dict(data_error=str(e),r=r))
        except IntegrityError, e:
            raise StorageIntegrityError(e.message)
            #api.abort(409, message=dict(integrity_error=e.message))
        except FlushError, e:
            api.abort(500, message=dict(flush_error=e.message))
        else:
            #Return a list of the response data, and max status code across all observations
            response = [ {'status': status, 'response': data, 'messages': messages} for (data,status,messages) in codes ]
        status_code = max( [ s for d,s,m in codes ] )
        return response, status_code
