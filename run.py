#!/bin/env python
from app import app,db,models

# useful tutorials:
# https://realpython.com/blog/python/flask-by-example-part-2-postgres-sqlalchemy-and-alembic/
# http://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iv-database
# for toolchains: http://addyosmani.com/blog/making-maven-grunt/

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])
