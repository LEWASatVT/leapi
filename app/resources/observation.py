from flask import request

from app import db
from app.models import Observation,Site,Sensor,Metric,Unit,Instrument,OffsetType
import app

from sqlalchemy.exc import IntegrityError,DataError

from flask.ext.restful import fields
from flask.ext.restful import reqparse
from flask.ext.restful import abort

from app.hal import HalResource, marshal_with

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

class ObservationResource(HalResource):
    fields = {
        'id': fields.Integer,
        'datetime': fields.DateTime,
        'value': fields.Float,
        'site_id': fields.String
    }
    
    _embedded = [ ('metric','CountedMetricResource'),
                  'instrument',
                  'sensor',
                  ('units', 'UnitResource'),
              ]
    #_embedded = { 'units': res.UnitResource,
    #              'metric': res.MetricResource,
    #              'instrument': res.InstrumentResource
    #              }

    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('value', type=float, required=True, help="value cannot be blank")
        self.parser.add_argument('datetime', type=str, required=True, help="missing datetime")
        self.parser.add_argument('units', type=dict, required=True, help="missing units")
        self.parser.add_argument('metric', type=dict, required=True, help="missing metric")
        self.parser.add_argument('instrument', type=dict, help="missing instrument")
        self.parser.add_argument('site', type=dict, help="missing site_id")
        self.parser.add_argument('sensor', type=dict) #TODO once established, make required 
        self.parser.add_argument('offset', type=dict)
        self.parser.add_argument('stderr', type=float)
        super(ObservationResource,self).__init__()

    @marshal_with(fields)
    def get(self, site_id, instrument_name, id = None):
        print("getting measurement for {} at {}".format(instrument_name,site_id))
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

    @marshal_with(fields)
    def post(self, site_id=None, instrument_id=None, instrument_name=None):
        if not request.json:
            abort(400, message="request must be JSON")
        errors = []

        args = self.parser.parse_args()
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
