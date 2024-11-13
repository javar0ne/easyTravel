from flask import Blueprint

organization = Blueprint(
    'organization',
    __name__,
    static_folder='static',
    template_folder='templates',
    url_prefix='/v1/organization'
)

from . import route