import itertools
import pytz
import logging
from datetime import datetime

from flask import request
from flask.ext.restplus import fields
from flask.ext.restful import abort,inputs

from sqlalchemy.exc import IntegrityError,DataError

from leapi.models import Observation,Site,Sensor,Metric,Unit,Instrument,CountedMetric
from leapi import api, hal
from leapi.hal import Resource
from leapi.resources import metric, unit, instrument
from leapi.dateparser import DateParser
from leapi.fields import Tuple

tz = pytz.timezone('US/Eastern')

data_sample_full = api.model('datasample', {
    'value': fields.Float(required=True),
    'stderr': fields.Float(),
    'datetime': fields.DateTime()
})

data_sample = Tuple(fields.Float(required=True), fields.DateTime('iso8601', required=True))
                    
parser = api.parser()
parser.add_argument('since', type=str, default='1 days', help='Return observations made since this date expression', location='args')
parser.add_argument('limit', type=int, help='Limit total number of observations returned to this integer', location='args')
parser.add_argument('interval', type=inputs.iso8601interval, help='An iso8601 formatted time interval')
parser.add_argument('method_id', type=int, help='Method id to filter by')

dateparser =  DateParser()

def make_ts(r, instrument_name, site_id, since, nodata=False):
    logging.info("making timeseries for instrument ({},{})".format(site_id,instrument_name))
    units = list(set([ o.units for o in r]))[0]
    metric = list(set([ o.metric for o in r]))[0]
    data = [] if nodata else [ (ob.value, ob.datetime) for ob in r ]

    instrument = Instrument.query.get([site_id,instrument_name])
    for o in [ metric, instrument ]:
        setattr(o,'site_id',site_id)
    ts = dict(data=data,
                instrument=instrument,
                metric=metric,
                metric_id=metric.id,
                units=units,
                site_id=site_id,
                since=since,
                length=len(data))
    if hasattr(metric, 'count'):
        ts['count']=metric.count

    return ts

@api.doc(params={'site_id': 'Site ID: obtained by following links from API root.', 'metric_id': 'Metric ID: obtained by following links from API root.'}, description=''' 
This is considered the primary resource for client use. The data
are returned in a structure that is relatively easy to process and
visualize.''')
class TimeseriesResource(Resource):
    '''This is the main resource for client visualization'''

    fields = api.model('TimeseriesResource', {
        'length': fields.Integer(),
        'since': fields.DateTime(),
        'data': fields.List(data_sample),
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
                     Observation.metric_id==Metric.id,
                     Metric.id==metric_id,
                     Observation.offset_value == 0]

        args = parser.parse_args()

        d = dateparser.parse(args['since'])
        if args['interval']:
            filterexp.append(Observation.datetime.between(*args['interval']))
            d = args['interval'][0]
        else:
            if d:
                filterexp.append(Observation.datetime>=d)
            else:
                abort(400, message="Could not parse date expression: '{}'".format(args['since']))

        #TODO: based on use of parse_args above, can probably clean
        #this up. Remember, argparse can have differnet
        #internal/external names too, which could be handy
        q = Observation.query.\
            filter(*filterexp).\
            order_by(Observation.instrument_name,Observation.datetime.desc())
        nodata = False
        if args['limit']:
            q = q.limit(args['limit'])
        if q.count() == 0:
            # If no results for this time period do a query for 1 observation
            # to populate unit,metric and instrument objects
            # TODO: If no observations exist for a site this will still
            # return an empty result
            filterexp.pop()
            q = Observation.query.join(Observation.metric,Site).\
            filter(*filterexp).limit(1)
            nodata = True
            
        r = q.all()
            
        grp = [ make_ts(list(k), g, site_id, since=d, nodata=nodata) for g,k in itertools.groupby(r,lambda x: x.instrument_name) ]
        grp = grp[0] if len(grp)==1 else grp
        return grp
