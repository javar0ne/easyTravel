from flask import Blueprint

itinerary = Blueprint(
    'itinerary',
    __name__,
    static_folder='static',
    template_folder='templates',
    url_prefix='/v1/itinerary'
)

from . import route