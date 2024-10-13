from datetime import datetime

from marshmallow import Schema, fields

COLLECTION_NAME = "travelers"

class Traveler:
    def __init__(
        self,
        phone_number: str = None,
        currency: str = None,
        name: str = None,
        surname: str = None,
        birth_date: datetime = None,
        interested_in: list[int] = list,
        user_id: str = None,
        _id: str = None
    ):
        self.phone_number = phone_number
        self.currency = currency
        self.name = name
        self.surname = surname
        self.birth_date = birth_date
        self.interested_in = interested_in
        self.user_id = user_id

    def to_dict(self):
        return {
            'phone_number': self.phone_number,
            'currency': self.currency,
            'name': self.name,
            'surname': self.surname,
            'birth_date': self.birth_date,
            'interested_in': self.interested_in,
            "user_id": self.user_id
        }

class TravelerCreateRequest(Schema):
    _id = fields.Str(dump_only=True)
    email = fields.Str(required=True)
    password = fields.Str(required=True)
    phone_number = fields.Str(required=True)
    currency = fields.Str(required=True)
    name = fields.Str(required=True)
    surname = fields.Str(required=True)
    birth_date = fields.DateTime(required=True)
    interested_in = fields.List(fields.Int(), required=True)

class TravelerUpdateRequest(Schema):
    _id = fields.Str(dump_only=True)
    email = fields.Str(required=True)
    phone_number = fields.Str(required=True)
    currency = fields.Str(required=True)
    name = fields.Str(required=True)
    surname = fields.Str(required=True)
    birth_date = fields.DateTime(required=True)
    interested_in = fields.List(fields.Int(), required=True)

class TravelerResponse(Schema):
    _id = fields.Str(required=True)
    email = fields.Str(required=True)
    phone_number = fields.Str(required=True)
    currency = fields.Str(required=True)
    name = fields.Str(required=True)
    surname = fields.Str(required=True)
    birth_date = fields.DateTime(required=True)
    interested_in = fields.List(fields.Int(), required=True)
