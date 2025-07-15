# encryption.py
"""Encryption and hashing utilities for user identifiers.

Provides AES-256 encryption for securely storing sensitive user data,
as well as SHA-256 hashing for efficient lookups and privacy-preserving
comparisons. Keys are loaded from a `.env` file.

Functions:
- encrypt(data): Encrypts a plaintext string using AES-CBC.
- decrypt(token): Decrypts a previously encrypted string.
- hash_user_id(user_id): Hashes a user ID using SHA-256.

Note:
The AES key must be exactly 32 bytes (256 bits), provided as a
hex string via the ENCRYPTION_KEY environment variable.
"""
import base64
import hashlib
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from config import ENCRYPTION_KEY

if ENCRYPTION_KEY is None:
    raise EnvironmentError("ENCRYPTION_KEY not set in environment.")
KEY = bytes.fromhex(ENCRYPTION_KEY)
if len(KEY) != 32:
    raise ValueError("ENCRYPTION_KEY must be 64 hex characters (256-bit key).")


def encrypt(data: str) -> str:
    """Encrypt a string using AES-256 in CBC mode with PKCS7 padding.

    Args:
        data (str): Plaintext string to encrypt.

    Returns:
        str: Base64-encoded ciphertext (includes IV + encrypted data).
    """
    iv = os.urandom(16)
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data.encode()) + padder.finalize()

    cipher = Cipher(algorithms.AES(KEY), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ct = encryptor.update(padded_data) + encryptor.finalize()

    return base64.b64encode(iv + ct).decode()


def decrypt(token: str) -> str:
    """Decrypt a Base64-encoded AES-256 encrypted string.

    Args:
        token (str): Base64-encoded ciphertext to decrypt.

    Returns:
        str: Decrypted plaintext string.
    """
    data = base64.b64decode(token.encode())
    iv, ct = data[:16], data[16:]

    cipher = Cipher(algorithms.AES(KEY), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ct) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    return (unpadder.update(padded_data) + unpadder.finalize()).decode()


def hash_user_id(user_id: str) -> str:
    """Hash a user ID using SHA-256.

    This hash is used for consent registry lookups.

    Args:
        user_id (str): Raw user ID string to hash.

    Returns:
        str: Hex-encoded SHA-256 hash of the user ID.
    """
    return hashlib.sha256(user_id.encode()).hexdigest()


def compute_row_hash(user_id_hash: str, message_enc: str) -> str:
    """Create a SHA-256 hash from a user hash and encrypted message.

    Args:
        user_id_hash (str): Hashed user ID.
        message_enc (str): Encrypted message content.

    Returns:
        str: A SHA-256 hex digest representing the row hash.
    """
    combined = user_id_hash + message_enc
    return hashlib.sha256(combined.encode()).hexdigest()
