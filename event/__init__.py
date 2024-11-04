from flask import Blueprint

event = Blueprint(
    'event',
    __name__,
    static_folder='static',
    template_folder='templates',
    url_prefix='/v1/event'
)

from . import route