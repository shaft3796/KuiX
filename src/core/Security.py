"""
This module implements a high-level abstraction of AES encryption, the encryption side of this module is not used
at the moment but this module is used to provide key generation for IPC security.
"""
from cryptography.fernet import Fernet


class Encryption:

    def __init__(self):
        # PLACEHOLDER
        self.cipher = None
        self.key = None

    def generate_key(self):
        self.key = Fernet.generate_key().decode()
        self.cipher = Fernet(self.key)
        return self.key

    def set_key(self, key: str):
        self.key = key
        self.cipher = Fernet(self.key)

    def encrypt(self, data: bytes):
        return self.cipher.encrypt(data)

    def decrypt(self, data: bytes):
        return self.cipher.decrypt(data)

    def encrypt_str(self, data: str):
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt_str(self, data: str):
        return self.cipher.decrypt(data.encode()).decode()

