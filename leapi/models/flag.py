from leapi import db
from leapi import hal
from sqlalchemy import UniqueConstraint

class Flag(db.Model):
    __tablename__ = 'flags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode, nullable=False)
    description = db.Column(db.Unicode)
    #site_id =
    #instrument_id = 
