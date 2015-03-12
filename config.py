import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URI']
    SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
    LOGFILE = os.environ.get('LEWAS_LOG_FILE', '/var/log/flask/leapi.log')
    MAGICSECRET='changethisafterssl'

class ProductionConfig(Config):
    DEBUG = False

class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    LOGGFILE = 'leapi_staging.log'

class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    SERVER_NAME = "localhost:5050"
    LOGGFILE = 'leapi.log'

class TestingConfig(Config):
    TESTING = True
