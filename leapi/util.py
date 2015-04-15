from itertools import islice

import logging

from leapi import app

def builderror_handler(error, endpoint, values):
    if app.debug:
        logging.error("url BuildError for endpoint {} with values {}".format(endpoint,values))
        return str(error)
    else:
        return "/404"

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

def window(seq, n=2):
    '''return a window of width in over iterator seq'''
    it = iter(seq)
    result = tuple(islice(it,n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result
