from sqlalchemy.orm import deferred

from leapi import db

class Media(db.Model):
    """Represents a media file"""

    id = db.Column(db.Integer(), primary_key = True)
    mime_type = db.Column(db.String(), nullable = False)
    data = deferred(db.Column(db.Binary()))
    user_id = db.Column(db.ForeignKey('users.id'), nullable = False)
    datetime = db.Column(db.DateTime(timezone=True))
    location_id = db.Column(db.ForeignKey('locations.id'))

    location = db.relationship('Location')
    user = db.relationship('User')
