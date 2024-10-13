COLLECTION_NAME = "users"

class User:
    def __init__(self, email: str, password: str, roles: list[str], _id: str = None):
        self._id = str(_id)
        self.email = email
        self.password = password
        self.roles = roles

    def to_dict(self):
        return {
            "email": self.email,
            "password": self.password,
            "roles": self.roles
        }

class Token:
    def __init__(self, access_token, refresh_token):
        self.access_token = access_token
        self.refresh_token = refresh_token

    def to_dict(self):
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token
        }