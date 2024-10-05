import os

def get_log_level():
     log_level = os.getenv('LOG_LEVEL')

     return log_level if log_level else 'DEBUG'

def configure_logging(app):
    log_level = get_log_level()
    app.logger.setLevel(log_level)

    app.logger.info('Logging enabled at level %s.', log_level)
