class User:
    def __init__(self, email: str, password: str, phone_number: str, currency: str, _id: str = None):
        self._id = _id
        self.email = email
        self.password = password
        self.phone_number = phone_number
        self.currency = currency