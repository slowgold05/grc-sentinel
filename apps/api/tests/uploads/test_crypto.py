from uuid import uuid4

import pytest
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ruleset.uploads.crypto import decrypt_upload, encrypt_upload


def test_envelope_encryption_is_tenant_bound_and_authenticated() -> None:
    org_id = uuid4()
    key = AESGCM.generate_key(bit_length=256)
    blob = encrypt_upload(b"sensitive policy", org_id, key)
    assert b"sensitive policy" not in blob.ciphertext
    assert decrypt_upload(blob, org_id, key) == b"sensitive policy"
    with pytest.raises(InvalidTag):
        decrypt_upload(blob, uuid4(), key)
