#!/bin/env python
from app import app,db,models
# import flask.ext.restless

# useful tutorials:
# https://realpython.com/blog/python/flask-by-example-part-2-postgres-sqlalchemy-and-alembic/
# http://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iv-database
# for toolchains: http://addyosmani.com/blog/making-maven-grunt/
def pre_get_many(**kw):
    print(kw)
    return kw

def post_get_many(**kw):
    print(kw['result']['objects'])
    kw['result']['_embedded'] = {'observation':  kw['result'].pop('objects')}
    return kw

def post_get_hal_links(**kw):
    kw['result']['_links'] = { 'self': '/observations' }
    kw

# manager = flask.ext.restless.APIManager(app, flask_sqlalchemy_db=db) #, postprocessors={ 'GET_MANY': [post_get_many, post_get_hal_links],
                                                                     #                 'GET_SINGLE': [post_get_hal_links ]})
# manager.create_api(models.Site, methods=['GET'])
# manager.create_api(models.Variable, methods=['GET'])
# manager.create_api(models.Observation, methods=['GET'], include_methods=["_links"])

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])
