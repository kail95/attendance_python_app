import secrets
import string

def generate_random_string(length=32):
    """Generate a securely random string of the given length."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))