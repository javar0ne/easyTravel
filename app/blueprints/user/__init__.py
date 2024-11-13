from flask import Blueprint


user = Blueprint(
    'user',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/v1/user'
)

from . import route