from leapi import db
from leapi import hal
from sqlalchemy import UniqueConstraint

groups_table = db.Table('group_metrics',
                        db.Column('group_id', db.Integer, db.ForeignKey('groups.id')),
                        db.Column('metric_id', db.Integer, db.ForeignKey('variables.id')),
                        db.Column('site_id', db.Unicode, db.ForeignKey('sites.id')),
                        db.Column('instrument_name', db.Integer),
                        UniqueConstraint('group_id','metric_id','site_id','instrument_name',name='unique_1')
              )

class Group(db.Model):
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode, nullable=False)
    description = db.Column(db.Unicode)
    site_id = db.Column(db.Unicode, db.ForeignKey('sites.id'))
    parent_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    
    children = db.relationship('Group', backref=db.backref('parent', remote_side=[id]))
    metrics = db.relationship('Metric', secondary=groups_table, backref='groups')

    def __unicode__(self):
        if self.metrics:
            return "{} ({}): {}".format(self.name, self.site_id, [ "{} {}".format(m.medium, m.name) for m in self.metrics])
        else:
            return "{}: parent of {}".format(self.name, [str(c.name) for c in self.children])

    def __str__(self):
        return unicode(self).encode('utf-8')

