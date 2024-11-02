class ElementAlreadyExistsException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class ElementNotFoundException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
