from leapi.models import Group

groups = Group.query.filter(Group.site_id=='stroubles1').all()

for g in groups:
    print(g)
