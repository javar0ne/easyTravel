from datetime import datetime

from marshmallow import Schema, fields

from common.user import User

COLLECTION_NAME = "travelers"

class Traveler(User):
    def __init__(
        self,
        email: str,
        password: str,
        phone_number: str,
        currency: str,
        name: str,
        surname: str,
        birth_date: datetime,
        interested_in: list[int],
        _id: int = None
    ):
        super().__init__(email, password, phone_number, currency, _id)
        self.name = name
        self.surname = surname
        self.birth_date = birth_date
        self.interested_in = interested_in

    def to_dict(self):
        return {
            'email': self.email,
            'password': self.password,
            'phone_number': self.phone_number,
            'currency': self.currency,
            'name': self.name,
            'surname': self.surname,
            'birth_date': self.birth_date,
            'interested_in': self.interested_in
        }

class TravelerSchema(Schema):
    _id = fields.Str(dump_only=True)
    email = fields.Str(required=True)
    password = fields.Str(required=True)
    phone_number = fields.Str(required=True)
    currency = fields.Str(required=True)
    name = fields.Str(required=True)
    surname = fields.Str(required=True)
    birth_date = fields.DateTime(required=True)
    interested_in = fields.List(fields.Int(), required=True)
