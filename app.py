from flask import Flask
from config.log import configure_logging

app = Flask(__name__)
configure_logging(app)

if __name__ == '__main__':
    app.run()
