from common.password_utils import hash_password


class User:
    def __init__(self, email: str, password: str, phone_number: str, currency: str, _id: int = None):
        self._id = _id
        self.email = email
        self.password = hash_password(password)
        self.phone_number = phone_number
        self.currency = currency