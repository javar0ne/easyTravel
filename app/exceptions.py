class OrganizationNotActiveException(Exception):
    def __init__(self):
        super().__init__("Organization selected not active!")
        self.message = "Organization disabled!"

class ElementAlreadyExistsException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class ElementNotFoundException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class KeyNotFoundException(Exception):
    def __init__(self):
        super().__init__("Key not found!")
        self.message = "Key not found!"