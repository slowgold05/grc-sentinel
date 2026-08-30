from hashlib import sha256
from io import BytesIO
from pathlib import PurePath
from zipfile import BadZipFile, ZipFile, is_zipfile

from pydantic import BaseModel

from ruleset.errors import InvalidUploadError

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_DOCX_EXPANDED_BYTES = 100 * 1024 * 1024
MAX_DOCX_ENTRIES = 10_000


class UploadMetadata(BaseModel):
    """Safe metadata derived from validated upload bytes."""

    filename: str
    media_type: str
    size: int
    sha256: str


def _validate_docx(content: bytes) -> None:
    try:
        with ZipFile(BytesIO(content)) as archive:
            entries = archive.infolist()
            names = {entry.filename for entry in entries}
            if len(entries) > MAX_DOCX_ENTRIES:
                raise InvalidUploadError("DOCX contains too many archive entries")
            if sum(entry.file_size for entry in entries) > MAX_DOCX_EXPANDED_BYTES:
                raise InvalidUploadError("DOCX expands beyond the allowed size")
            if any(entry.flag_bits & 1 for entry in entries):
                raise InvalidUploadError("encrypted DOCX files are not supported")
            if any(PurePath(entry.filename).is_absolute() or ".." in PurePath(entry.filename).parts for entry in entries):
                raise InvalidUploadError("DOCX contains an unsafe archive path")
            if not {"[Content_Types].xml", "word/document.xml"} <= names:
                raise InvalidUploadError("ZIP file is not a DOCX document")
    except BadZipFile as error:
        raise InvalidUploadError("invalid DOCX archive") from error


def validate_upload(filename: str, content: bytes) -> UploadMetadata:
    """Validate an untrusted PDF or DOCX before parsing or storage."""
    if not filename or len(filename) > 255 or PurePath(filename).name != filename or "\x00" in filename:
        raise InvalidUploadError("invalid filename")
    if not content:
        raise InvalidUploadError("upload is empty")
    if len(content) > MAX_UPLOAD_BYTES:
        raise InvalidUploadError("upload exceeds 20 MiB")

    suffix = PurePath(filename).suffix.lower()
    if content.startswith(b"%PDF-"):
        media_type = "application/pdf"
        expected_suffix = ".pdf"
    elif is_zipfile(BytesIO(content)):
        _validate_docx(content)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        expected_suffix = ".docx"
    else:
        raise InvalidUploadError("unsupported file signature")
    if suffix != expected_suffix:
        raise InvalidUploadError("filename extension does not match file content")

    return UploadMetadata(
        filename=filename,
        media_type=media_type,
        size=len(content),
        sha256=sha256(content).hexdigest(),
    )

