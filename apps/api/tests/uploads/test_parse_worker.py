from io import BytesIO
from zipfile import ZipFile

from ruleset.uploads.parse_worker import parse_document
from ruleset.uploads.validation import validate_upload


def test_extracts_docx_text_in_worker() -> None:
    payload = BytesIO()
    with ZipFile(payload, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr(
            "word/document.xml",
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            "<w:body><w:p><w:r><w:t>Access policy</w:t></w:r></w:p></w:body></w:document>",
        )
    content = payload.getvalue()
    metadata = validate_upload("policy.docx", content)
    result = parse_document(content, metadata.media_type)
    assert [(section.seq, section.text) for section in result.sections] == [(1, "Access policy")]
