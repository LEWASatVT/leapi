from flask import request

from sqlalchemy.exc import IntegrityError,DataError
from sqlalchemy.orm.exc import FlushError

from flask.ext.restplus import fields, Resource
from flask.ext.restful import abort

from leapi import db, app, api, hal
from leapi.models import Observation,Site,Sensor,Metric,CountedMetric,Unit,Instrument,OffsetType
from leapi.resources import metric, unit, instrument, sensor

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
parser.add_argument('datetime', type=str, required=True, help="date and time observation was made", location='json')
parser.add_argument('units', type=dict, required=True, help="units observation value is in", location='json')
parser.add_argument('metric', type=dict, required=True, help="metric the observation observed", location='json')
parser.add_argument('instrument', type=dict, help="instrument that made the observation")
parser.add_argument('site', type=dict, help="missing site_id", location='json')
parser.add_argument('sensor', type=dict) #TODO once established, make required 
parser.add_argument('offset', type=dict, help="physical or temporal offset of observed value", location='json')
parser.add_argument('stderr', type=float, help="standard deviation of observed value", location='json')
parser.add_argument('magicsecret', default='magicsecret', type=str)

#parser = api.parser()
#parser.add_argument('body', type=dict, required=True, help="Body of request", location="json")

observation_model = api.model('BaseObservation',
                              {
                                  'datetime': fields.DateTime(required=True, description='A formated datetime string'),
                                  'value': fields.Float(required=True),
                                  'offset': fields.Nested(api.model('offset', {'value': fields.Float(), 'type': fields.String(enum=['A','B'])})), 
                                  'stderr': fields.Float(description='Standard error associated with value'),
                                  'site_id': fields.String(required=True)
                              })

get_fields = api.extend('Observation', observation_model, 
                        {
                            'id': fields.Integer(),
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

# TODO: When we get materialized views working on server we can use CountedMetricResource
_embedded = { 'metric': metric.MetricResource.fields,
              'units': unit.UnitResource.fields,
              'instrument': instrument.InstrumentResource.fields,
              'sensor': sensor.SensorResource.fields
}

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

    if not args['magicsecret'] == app.config['MAGICSECRET']:
        if args['magicsecret'] == 'ssldebugtest':
            print("ssl debug mode")
            #engage super secret ssl diagnostics mode!
            print str(args['CLIENT_VERIFY']) + str(args['CLIENT_CERT'])
        return (r, 403, [])

    site = Site.query.get(site_id)

    #instrument = Instrument.query.filter(Site.id==site.id, Instrument.name==instrument_name).first()

    # TODO: When materialize views are implemented we can use CountedMetric
    metric = by_id_or_filter(Metric, args, 'metric')
    unit = Unit.query.filter_by(abbv=args['units']['abbv']).first()
    #sensor = by_id_or_filter(Sensor, args)

    if site == None:
        messages.append("No site with: {}".format(args['site']))
    if unit == None:
        messages.append("No unit with abbv: {}".format(args['units']['abbv']))
    if metric == None:
        messages.append("No metric with: {}".format(args['metric']))
    if len(messages) > 0:
        print("errors: {}".format(messages))
        return (r, 400, messages)

    r = Observation(datetime=args['datetime'], value=args['value'], site_id=site_id)

    r.site_id = site.id
    r.site = site
    #r.instrument = instrument
    r.instrument_name = instrument_name
    #r.instrument_id = instrument.id
    r.metric = metric
    r.metric_id = metric.id
    r.units = unit
    r.stderr = args['stderr']
    if args['offset']:
        offset = OffsetType.query.filter_by(description=args['offset']['type']).first()
        r.offset_value = args['offset']['value']
        r.offset_type_id = offset.id
    return (r, 201, messages)

    #@api.doc(params={'site_id': 'A site ID', 'instrument_id': 'An instrument ID'})
class ObservationResource(Resource):
    '''Show a single observation made or post a new one. Primary resource used by sensor layer'''

    fields=get_fields
    
    @hal.marshal_with(fields, embedded=_embedded)
    @api.doc(description="Not particularly useful for timeseries analysis, that's what the timeseries resource is for")
    def get(self, site_id, instrument_name=None, instrument_id=None, id = None):
        '''get a particular observation or list of observations. Not terribly useful, you probably want timeseries'''

        #don't really need to check for an instrument specifier,
        #observation ids are unique and the routing rules only allow
        #URIs with instrument identifiers.

        #if not (instrument_name or instrument_id):
        #    api.abort(400)
        filterexp = [Site.id==site_id,Instrument.name==instrument_name,Observation.site_id==site_id,Observation.instrument_id==Instrument.id]
        if 'metric' in ( k.split('.')[0] for k in request.args.keys() ):
            mkeys = [ k.split('.')[1] for k in request.args.keys() if k.split('.')[0] == 'metric' ]
            filter_by = dict([ (k.split('.')[1], v) for k,v in request.args.items() if k.split('.')[0] == 'metric' ])
            r = Observation.query.join(Site,Instrument,Observation.metric).filter(*filterexp).limit(200).all()
        elif id == None:
            r = Observation.query.join(Site,Instrument).filter(*filterexp).order_by(Observation.datetime.desc()).limit(200).all()
        else:
            r = Observation.query.get_or_404(id)
        return r

class ObservationList(Resource):
    fields=get_fields
    
    @api.doc(responses={201: 'Observation created'}, description="Only enough fields in the embedded resources units,metric and instrument need be provided to identify an existing record")
    @api.marshal_list_with(observation_response, code=201)
    @api.expect(post_fields)
    def post(self, site_id, instrument_name):
        '''Post a new observation'''
        if not request.json:
            print("request was not JSON")
            abort(400, message="request must be JSON")
        errors = []
        codes = []
        
        if isinstance(request.json, list):
            codes = [ prep_observation(o, site_id, instrument_name) for o in request.json]
                
        else:
            codes = [ prep_observation(request.json, site_id, instrument_name) ]

        for (r,code,errors) in codes:
            if code == 201:
                db.session.add(r)

        #TODO: On some of these errors, IntegrityError in particular, it may make sense
        #to go back and try each observation as a separate commit to find the one that caused the error
        #then update the returned status
        try:
            db.session.commit()
        except DataError, e:
            abort(400, message=dict(data_error=str(e),r=r))
        except IntegrityError, e:
            print("IntegrityError: {}".format(e))
            abort(409, message=dict(integrity_error=e.message))
        except FlushError, e:
            abort(500, message=dict(flush_error=e.message))
        else:
            #Return a list of the response data, and max status code across all observations
            response = [ {'status': status, 'response': data, 'messages': messages} for (data,status,messages) in codes ]
        return response, max( [ s for d,s,m in codes ] )
