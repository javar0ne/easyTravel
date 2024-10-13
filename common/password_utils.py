from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(password: str) -> str:
    """Hashes the given password using Werkzeug's generate_password_hash."""
    return generate_password_hash(password)

def check_password(hashed_password: str, plain_password: str) -> bool:
    """Verifies if the hashed password matches the plain password."""
    return check_password_hash(hashed_password, plain_password)