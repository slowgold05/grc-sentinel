from io import BytesIO
from zipfile import ZipFile

import pytest

from ruleset.errors import InvalidUploadError
from ruleset.uploads.validation import validate_upload


def _docx() -> bytes:
    payload = BytesIO()
    with ZipFile(payload, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<document/>")
    return payload.getvalue()


def test_validates_magic_bytes_and_docx_structure() -> None:
    pdf = validate_upload("policy.pdf", b"%PDF-1.7\n%%EOF")
    docx = validate_upload("policy.docx", _docx())
    assert pdf.media_type == "application/pdf"
    assert docx.media_type.endswith("wordprocessingml.document")

    with pytest.raises(InvalidUploadError):
        validate_upload("policy.pdf", _docx())
    with pytest.raises(InvalidUploadError):
        validate_upload("../policy.pdf", b"%PDF-1.7")
    with pytest.raises(InvalidUploadError):
        validate_upload("fake.docx", b"PK-not-a-real-archive")
