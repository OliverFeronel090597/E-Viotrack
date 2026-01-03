import hashlib

def hash_password(password: str):
    # Use a strong hashing algorithm (e.g., sha256)
    hash_object = hashlib.sha256(password.encode('utf-8'))
    hex_dig = hash_object.hexdigest()
    return hex_dig