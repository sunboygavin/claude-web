"""
Security module for MCP credential encryption and decryption.
Uses Fernet (AES-256) symmetric encryption.
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os


class CredentialEncryption:
    """Handles encryption and decryption of MCP server credentials."""

    def __init__(self, secret_key: str):
        """
        Initialize encryption with a secret key.

        Args:
            secret_key: Flask SECRET_KEY or similar secret
        """
        self.secret_key = secret_key
        self._fernet = None

    def _get_fernet(self) -> Fernet:
        """Get or create Fernet instance with derived key."""
        if self._fernet is None:
            # Derive a key from the secret key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'claude-web-mcp-salt',  # Static salt for consistency
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(
                kdf.derive(self.secret_key.encode())
            )
            self._fernet = Fernet(key)
        return self._fernet

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext credential.

        Args:
            plaintext: The credential value to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return ""

        fernet = self._get_fernet()
        encrypted = fernet.encrypt(plaintext.encode())
        return encrypted.decode()

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an encrypted credential.

        Args:
            ciphertext: The encrypted credential value

        Returns:
            Decrypted plaintext string
        """
        if not ciphertext:
            return ""

        fernet = self._get_fernet()
        decrypted = fernet.decrypt(ciphertext.encode())
        return decrypted.decode()

    def encrypt_dict(self, data: dict) -> dict:
        """
        Encrypt all string values in a dictionary.

        Args:
            data: Dictionary with plaintext values

        Returns:
            Dictionary with encrypted values
        """
        encrypted = {}
        for key, value in data.items():
            if isinstance(value, str):
                encrypted[key] = self.encrypt(value)
            else:
                encrypted[key] = value
        return encrypted

    def decrypt_dict(self, data: dict) -> dict:
        """
        Decrypt all string values in a dictionary.

        Args:
            data: Dictionary with encrypted values

        Returns:
            Dictionary with decrypted values
        """
        decrypted = {}
        for key, value in data.items():
            if isinstance(value, str):
                try:
                    decrypted[key] = self.decrypt(value)
                except Exception:
                    # If decryption fails, assume it's not encrypted
                    decrypted[key] = value
            else:
                decrypted[key] = value
        return decrypted


# Global instance (will be initialized with Flask SECRET_KEY)
_encryption_instance = None


def init_encryption(secret_key: str):
    """Initialize the global encryption instance."""
    global _encryption_instance
    _encryption_instance = CredentialEncryption(secret_key)


def get_encryption() -> CredentialEncryption:
    """Get the global encryption instance."""
    if _encryption_instance is None:
        raise RuntimeError("Encryption not initialized. Call init_encryption() first.")
    return _encryption_instance
