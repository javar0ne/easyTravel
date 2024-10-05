from flask import Flask
from config.logging import configure_logging

app = Flask(__name__)
configure_logging(app)

@app.route('/')
def handle_hello_world():
    return 'Hello World!'

if __name__ == '__main__':
    app.run()
