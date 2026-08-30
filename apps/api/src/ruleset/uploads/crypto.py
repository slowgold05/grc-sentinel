from base64 import urlsafe_b64decode
from os import urandom
from uuid import UUID

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pydantic import BaseModel


class EncryptedBlob(BaseModel):
    """Ciphertext plus the wrapped per-upload data key."""

    ciphertext: bytes
    nonce: bytes
    wrapped_key: bytes
    key_nonce: bytes


def decode_master_key(encoded: str) -> bytes:
    """Decode and validate a URL-safe base64 256-bit master key."""
    key = urlsafe_b64decode(encoded)
    if len(key) != 32:
        raise ValueError("upload master key must decode to 32 bytes")
    return key


def encrypt_upload(content: bytes, org_id: UUID, master_key: bytes) -> EncryptedBlob:
    """Encrypt bytes with a random data key wrapped by the configured master key."""
    data_key, nonce, key_nonce = AESGCM.generate_key(bit_length=256), urandom(12), urandom(12)
    aad = org_id.bytes
    return EncryptedBlob(
        ciphertext=AESGCM(data_key).encrypt(nonce, content, aad),
        nonce=nonce,
        wrapped_key=AESGCM(master_key).encrypt(key_nonce, data_key, aad),
        key_nonce=key_nonce,
    )


def decrypt_upload(blob: EncryptedBlob, org_id: UUID, master_key: bytes) -> bytes:
    """Authenticate and decrypt one tenant-bound upload."""
    aad = org_id.bytes
    data_key = AESGCM(master_key).decrypt(blob.key_nonce, blob.wrapped_key, aad)
    return AESGCM(data_key).decrypt(blob.nonce, blob.ciphertext, aad)

