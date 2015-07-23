from leapi import db
from geoalchemy2.types import Geography

# on apt-get systems do a apt-get install postgis* to get all needed packages
# then, 'psql -d [database name] -c "CREATE EXTENSION postgis;"'

class Location(db.Model):
    __tablename__ = 'locations'

    def __init__(self, **kwargs):
        geo = 'POINT({} {} {})'.format(kwargs['latitude'],kwargs['longitude'],kwargs['altitude'])
        self.geo = geo

    id = db.Column(db.Integer(), primary_key=True)
    geo = db.Column(Geography(geometry_type='POINTZ',dimension=3))
