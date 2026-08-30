from collections.abc import Mapping

from pydantic import BaseModel


REQUIRED_HEADERS = {
    "content-security-policy": "CSP",
    "strict-transport-security": "HSTS",
    "x-content-type-options": "X-Content-Type-Options",
    "x-frame-options": "X-Frame-Options",
}


class HeaderPosture(BaseModel):
    """Deterministic security-header posture from one public homepage response."""

    present: list[str]
    missing: list[str]
    grade: str


def grade_security_headers(headers: Mapping[str, str]) -> HeaderPosture:
    """Grade presence of four broadly applicable browser security headers."""
    # ponytail: presence-only grade; validate directive strength when false positives matter.
    names = {name.lower() for name in headers}
    present = [label for name, label in REQUIRED_HEADERS.items() if name in names]
    missing = [label for name, label in REQUIRED_HEADERS.items() if name not in names]
    grade = ("F", "D", "C", "B", "A")[len(present)]
    return HeaderPosture(present=present, missing=missing, grade=grade)
