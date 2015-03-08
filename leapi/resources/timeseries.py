import itertools

import pytz

from flask import request
from flask.ext.restplus import fields
from flask.ext.restful import abort

from sqlalchemy.exc import IntegrityError,DataError

from leapi.models import Observation,Site,Sensor,Metric,Unit,Instrument,CountedMetric
from leapi import api, hal
from leapi.hal import Resource
from leapi.resources import metric, unit, instrument
from leapi.dateparser import DateParser

TZ = pytz.timezone('US/Eastern')

def make_ts(r, instrument_id, site_id):
    units = list(set([ o.units for o in r]))[0]
    metric = list(set([ o.metric for o in r]))[0]
    data = [ (ob.value, ob.datetime.isoformat()) for ob in r ]
    instrument = Instrument.query.get(instrument_id)
    for o in [ metric, instrument ]:
        setattr(o,'site_id',site_id)
    return dict(data=data,
                instrument=instrument,
                metric=metric,
                metric_id=metric.id,
                units=units,
                site_id=site_id,
                length=len(data),
                count=metric.count)

parser = api.parser()
parser.add_argument('since', type=str, default='2 day', help="Return observations made since this date expression")
parser.add_argument('limit', type=int, help="Limit total number of observations returned to this integer")

dateparser =  DateParser()

        #@api.doc(params={'site_id': 'Site ID', 'metric_id': 'Metric ID'})
class TimeseriesResource(Resource):
    '''This is the main resource for client visualization'''
    fields = api.model('TimeseriesResource', {
        'length': fields.Integer(),
        'data': fields.Raw(),
    })

    _embedded = { 'metric': metric.MetricResource.fields,
                  'units': unit.UnitResource.fields,
                  'instrument': instrument.InstrumentResource.fields
              }


    @hal.marshal_with(fields,embedded=_embedded)
    @api.doc(parser=parser, responses={200: 'timeseries retreived', 400: 'bad request'})
    def get(self, site_id, metric_id):
        '''retreive a timeseries of observed values for a given metric'''
        #print("my endpoint is {}".format(self.endpoint))
        #print("my url is {}".format(api.url_for(self, site_id='stroubles1')))
        data = []
        filterexp = [Site.id==site_id,
                     Observation.site_id==Site.id,
                     Observation.instrument_id==Instrument.id,
                     Observation.metric_id==Metric.id,
                     Metric.id==metric_id,
                     Observation.offset_value == None]
        args = parser.parse_args()

        d = dateparser.parse(args['since'])
        if d:
            filterexp.append(Observation.datetime>=d)
        else:
            abort(400, message="Could not parse date expression: '{}'".format(args['since']))

        #TODO: based on use of parse_args above, can probably clean
        #this up. Remember, argparse can have differnet
        #internal/external names too, which could be handy
        q = Observation.query.join(Observation.metric,Site,Instrument).\
            filter(*filterexp)#.\
            #order_by(Observation.instrument_id,Observation.datetime.desc()).\
            #group_by(Observation.instrument_id,Observation.id)
        if args['limit']:
            q = q.limit(args['limit'])
        r = q.all()

        grp = [ make_ts(list(k),g,site_id) for g,k in itertools.groupby(r,lambda x: x.instrument_id) ]
        grp = grp[0] if len(grp)==1 else grp
        return grp
