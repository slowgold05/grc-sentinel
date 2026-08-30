class UnknownRegulationError(ValueError):
    """Raised when a determination references regulation data not in the knowledge base."""


class InvalidUploadError(ValueError):
    """Raised when an uploaded file fails boundary validation."""


class DocumentParseError(ValueError):
    """Raised when the isolated document parser fails or exceeds a limit."""

