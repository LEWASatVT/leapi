import logging

from leapi import app

def builderror_handler(error, endpoint, values):
    if app.debug:
        logging.error("url BuildError for endpoint {} with values {}".format(endpoint,values))
        return str(error)
    else:
        return None

app.url_build_error_handlers.append(builderror_handler)

if not app.debug:
    import logging
    from logging import handlers
    file_handler = handlers.RotatingFileHandler(app.config.get('LOGFILE', '/var/log/flask/leapi.log'))
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)

    from logging import Formatter
    file_handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))

