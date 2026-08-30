from io import BytesIO
import multiprocessing
from queue import Empty
from zipfile import ZipFile

from defusedxml import ElementTree
from pydantic import BaseModel
from pypdf import PdfReader

from ruleset.errors import DocumentParseError

MAX_PAGES = 200
MAX_TEXT_CHARS = 2_000_000
WORKER_MEMORY_BYTES = 256 * 1024 * 1024


class DocumentSection(BaseModel):
    """One ordered page or paragraph extracted from a document."""

    seq: int
    text: str


class ParsedDocument(BaseModel):
    """Length-capped text extracted by the isolated worker."""

    sections: list[DocumentSection]


def _limit_memory() -> None:
    try:
        import resource
    except ImportError:
        # ponytail: Windows lacks resource limits; deploy parser in its own capped container.
        return
    resource.setrlimit(resource.RLIMIT_AS, (WORKER_MEMORY_BYTES, WORKER_MEMORY_BYTES))


def _pdf_sections(content: bytes) -> list[str]:
    reader = PdfReader(BytesIO(content))
    if reader.is_encrypted:
        raise DocumentParseError("encrypted PDFs are not supported")
    if len(reader.pages) > MAX_PAGES:
        raise DocumentParseError("PDF exceeds 200 pages")
    return [page.extract_text() or "" for page in reader.pages]


def _docx_sections(content: bytes) -> list[str]:
    with ZipFile(BytesIO(content)) as archive:
        root = ElementTree.fromstring(archive.read("word/document.xml"))
    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    return [
        "".join(node.text or "" for node in paragraph.iter(f"{namespace}t"))
        for paragraph in root.iter(f"{namespace}p")
    ]


def _parse(content: bytes, media_type: str, output: multiprocessing.Queue) -> None:
    _limit_memory()
    try:
        sections = (
            _pdf_sections(content)
            if media_type == "application/pdf"
            else _docx_sections(content)
        )
        if sum(map(len, sections)) > MAX_TEXT_CHARS:
            raise DocumentParseError("extracted text exceeds the allowed size")
        output.put(("ok", sections))
    except Exception as error:
        output.put(("error", type(error).__name__))


def parse_document(content: bytes, media_type: str, *, timeout_seconds: float = 10) -> ParsedDocument:
    """Extract text in a killable child process with hard output limits."""
    if media_type not in {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }:
        raise DocumentParseError("unsupported media type")
    context = multiprocessing.get_context("spawn")
    output = context.Queue(maxsize=1)
    process = context.Process(target=_parse, args=(content, media_type, output))
    process.start()
    process.join(timeout_seconds)
    if process.is_alive():
        process.terminate()
        process.join()
        raise DocumentParseError("document parsing timed out")
    try:
        status, result = output.get(timeout=1)
    except Empty as error:
        raise DocumentParseError("document parser exited without a result") from error
    finally:
        output.close()
    if status == "error":
        raise DocumentParseError(f"document parser rejected input: {result}")
    return ParsedDocument(
        sections=[DocumentSection(seq=index, text=text) for index, text in enumerate(result, 1)]
    )
