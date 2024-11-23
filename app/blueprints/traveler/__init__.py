from flask import Blueprint

traveler = Blueprint(
    'traveler',
    __name__,
    static_folder='static',
    template_folder='templates',
    url_prefix='/v1/traveler'
)

from . import route