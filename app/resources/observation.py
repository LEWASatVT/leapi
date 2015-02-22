from flask import request

from app import db
from app.models import Observation,Site,Sensor,Metric,Unit,Instrument
import app

from sqlalchemy.exc import IntegrityError,DataError

from flask.ext.restful import fields
from flask.ext.restful import reqparse
from flask.ext.restful import abort

from app.hal import HalResource, marshal_with

def by_id_or_filter(obj, args):
    atname = obj.__name__.lower()
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
        super(ObservationResource,self).__init__()

    @marshal_with(fields)
    def get(self, id = None):
        if 'metric' in ( k.split('.')[0] for k in request.args.keys() ):
            mkeys = [ k.split('.')[1] for k in request.args.keys() if k.split('.')[0] == 'metric' ]
            filter_by = dict([ (k.split('.')[1], v) for k,v in request.args.items() if k.split('.')[0] == 'metric' ])
            r = Observation.query.join(Observation.metric).filter_by(**filter_by).limit(200).all()
        elif id == None:
            r = Observation.query.order_by(Observation.datetime.desc()).limit(200).all()
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
        db.session.add(r)
        try:
            db.session.commit()
        except DataError, e:
            abort(400, message=dict(data_error=str(e),r=r))
        except IntegrityError, e:
            abort(409, message=dict(integrity_error=e.message))
        return r, 201
