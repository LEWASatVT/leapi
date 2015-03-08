from flask import request

from sqlalchemy.exc import IntegrityError,DataError

from flask.ext.restplus import fields, Resource
from flask.ext.restful import abort

from leapi import db, api, hal
from leapi.models import Observation,Site,Sensor,Metric,Unit,Instrument,OffsetType
from leapi.resources import metric, unit, instrument, sensor

def by_id_or_filter(obj, args, atname=None):
    atname = obj.__name__.lower() if atname == None else atname
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
parser.add_argument('offset', type=dict, help="physical or temperal offset of observed value")
parser.add_argument('stderr', type=float, help="standard deviation of observed value")

#@api.doc(params={'site_id': 'A site ID', 'instrument_id': 'An instrument ID'})
class ObservationResource(Resource):
    '''Show a single observation made or post a new one. Primary resource used by sensor layer'''
    fields = api.model('Observation',
                       {
                           'id': fields.Integer(),
                           'datetime': fields.DateTime(required=True, description='A formated datetime string'),
                           'value': fields.Float(required=True),
                           'offset': fields.Nested(api.model('offset', {'value': fields.Float(), 'type': fields.String()})), 
                           'site_id': fields.String(required=True)
                       })

    _embedded = { 'metric': metric.MetricResource.fields,
                  'units': unit.UnitResource.fields,
                  'instrument': instrument.InstrumentResource.fields,
                  'sensor': sensor.SensorResource.fields
              }

    @hal.marshal_with(fields, embedded=_embedded)
    @api.doc(description="Not particularly useful for timeseries analysis, that's what the timeseries resource is for")
    def get(self, site_id, instrument_name, id = None):
        '''get a particular observation or list of observations. Not terribly useful, you probably want timeseries'''
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

    @api.doc(responses={201: 'Observation created'}, parser=parser)
    @api.marshal_with(fields, code=201)
    def post(self, site_id=None, instrument_id=None, instrument_name=None):
        '''Post a new observation'''
        if not request.json:
            abort(400, message="request must be JSON")
        errors = []

        args = parser.parse_args()
        r = Observation(datetime=args['datetime'], value=args['value'])
        if site_id:
            site = Site.query.get(site_id)
        else:
            site = by_id_or_filter(Site, args)

        if instrument_id and instrument_name:
            abort(409, message="supply either instrument id OR instrument name")

        if instrument_name:
            instrument = Instrument.query.filter(Site.id==site.id, Instrument.name==instrument_name).first()
        elif instrument_id:
            instrument = Instrument.query.get(instrument_id)
        else:
            instrument = by_id_or_filter(Instrument, args)

        metric = by_id_or_filter(Metric, args)
        unit = Unit.query.filter_by(abbv=args['units']['abbv']).first()
        sensor = by_id_or_filter(Sensor, args)
        
        if site == None:
            errors.append("No site with: {}".format(args['site']))
        if unit == None:
            errors.append("No unit with abbv: {}".format(args['units']['abbv']))
        if instrument == None:
            errors.append("No instrument with: {}".format(args['instrument']))
        if metric == None:
            errors.append("No metric with: {}".format(args['metric']))
        if len(errors) > 0:
            print("errors: {}".format(errors))
            abort(400, message=errors)

        if sensor == None:
            #try to get sensor by args[sensor] 
            #try to get sensor by name and instrument
            sensor = Sensor.query.filter(Sensor.name==metric.name,Sensor.instrument_id==instrument.id).first()
            if not sensor:
                sensor = Sensor(name=metric.name)
                sensor.metric=metric
                sensor.instrument=instrument
                db.session.add(sensor)
                try:
                    db.session.commit()
                except DataError as e:
                    abort(400, message=dict(data_error=str(e)))
                except IntegrityError as e:
                    abort(409, message=dict(integrity_error=str(e)))
            
            #return dict(messages=errors), 400
        r.site_id = site.id
        r.site = site
        r.instrument = instrument
        r.instrument_id = instrument.id
        r.sensor_id = sensor.id
        r.metric = metric
        r.metric_id = metric.id
        r.units = unit
        r.stderr = args['stderr']
        if args['offset']:
            offset = OffsetType.query.filter_by(description=args['offset']['type']).first()
            r.offset_value = args['offset']['value']
            r.offset_type_id = offset.id

        #r.offset_value = args['offset_value']
        #r.offset_type = OffsetType.query.get(args['offset_type']['id'])

        db.session.add(r)
        try:
            db.session.commit()
        except DataError, e:
            abort(400, message=dict(data_error=str(e),r=r))
        except IntegrityError, e:
            abort(409, message=dict(integrity_error=e.message))
        return r, 201
