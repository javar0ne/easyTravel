import os

from flask import Flask
from traveler import traveler

app = Flask(__name__)
app.register_blueprint(traveler)


def get_logging_level():
    log_level = os.getenv('LOG_LEVEL')
    return log_level if log_level else 'DEBUG'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')