from app import db
from app import hal
from sqlalchemy import UniqueConstraint

groups = db.Table('group_metrics',
                  db.Column('group_id', db.Integer, db.ForeignKey('groups.id')),
                  db.Column('metric_id', db.Integer, db.ForeignKey('metrics.id')),
                  db.Column('instrument_id', db.Interger, db.ForeignKey('instruments.id'))
              )

class Group(db.Model):
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode, nullable=False)
    description = db.Column(db.Unicode)
    parent_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    
