import os

def get_logging_level():
     log_level = os.getenv('LOG_LEVEL')

     return log_level if log_level else 'DEBUG'

def configure_logging(app):
    logging_level = get_logging_level()
    app.logger.setLevel(logging_level)

    app.logger.info('Logging enabled at level %s.', logging_level)
