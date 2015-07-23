from sqlalchemy.exc import IntegrityError
from flask import g
from flask.ext.restplus import fields, Resource
from flask.ext.restful import inputs
from os import path
from datetime import datetime

import json

from leapi import db, api, app
from leapi.security import auth
from leapi.models import Media, Location
from leapi.resources import MediaContentResource

class LocationField(fields.Raw):
    def format(self,value):
        print("media location: {}".format(db.session.scalar(value.ST_AsGeoJSON())))
        return json.loads(db.session.scalar(value.ST_AsGeoJSON()))

class User(fields.Raw):
    def format(self,value):
        return value.email

geolocation = api.model('GeoLocation', {
    'geo': LocationField,
    })

fields = api.model('Media', {
    'mime_type': fields.String,
    'datetime': fields.DateTime(required=True, description='Date and time media was created'),
    'location': fields.Nested(geolocation),
    'href': fields.String,
    'user': User
})

import geojson,json

def geolocation(obj):
    #validate = geojson.is_valid(geojson.loads(json.dumps(obj)))
    #print('validate: {}'.format(validate))
    #if validate['valid']=='no':
    #    print('{} is not valid geoJSON: {}'.format(json.dumps(obj),validate['message']))
    #    raise ValueError('{} is not valid geoJSON: {}'.format(json.dumps(obj),validate['message']))
    return obj #TODO: validate values for lat, long and alt

parser = api.parser()
parser.add_argument('datetime', type=inputs.datetime_from_iso8601, required=True, help='date the media was created')
parser.add_argument('mime_type', type=inputs.regex('image/[a-z]'), required=True, help='media mime time, currently must be some kind of image') 
parser.add_argument('geolocation', type=geolocation, help='location media is associated with')

def create_location(args):
    locstr = 'POINT({} {} {})'.format(*args['coordinates'])
    loc = Location.query.filter(Location.geo==locstr).first()
    if not loc: 
        loc = Location(latitude=args['latitude'], longitude=args['longitude'], altitude=args['altitude'])
        db.session.add(loc)
        db.session.commit()

    return loc

def create_media(args):
    media = Media(mime_type=args.mime_type, datetime=args.datetime)
    if args.geolocation:
        media.location = create_location(args.geolocation)
    media.href = path.join(app.config.get('MEDIA_ROOT'), datetime.strftime(args.datetime, '%Y%m%dT%H%M%S%z'))
    media.user = g.user
    db.session.add(media)
    try:
        db.session.commit()
    except IntegrityError as e:
        api.abort(400, message=str(e))
    media.href = api.url_for(MediaContentResource, id=media.id)
    return media

class MediaResource(Resource):
    def get(self, id):
        r = Media.query.get_or_404(id)
        return r

class MediaListResource(Resource):
    @api.marshal_with(fields, as_list=True)
    def get(self):
        q = Media.query

        return q.all()

    @auth.login_required
    @api.marshal_with(fields)
    def post(self):
        args = parser.parse_args()
        media = create_media(args)
        return media
