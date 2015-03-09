from leapi import db
from leapi import hal
from sqlalchemy import UniqueConstraint

groups = db.Table('group_metrics',
                  db.Column('group_id', db.Integer, db.ForeignKey('groups.id')),
                  db.Column('metric_id', db.Integer, db.ForeignKey('variables.id')),
                  db.Column('site_id', db.Unicode, db.ForeignKey('sites.id')),
                  db.Column('instrument_name', db.Integer)
              )

class Group(db.Model):
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode, nullable=False)
    description = db.Column(db.Unicode)
    site_id = db.Column(db.Unicode, db.ForeignKey('sites.id'))
    parent_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    
