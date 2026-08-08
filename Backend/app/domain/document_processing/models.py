"""Standard document processing models (ADR-002).

These are pure data structures that flow between the PDF reader, the document
detector and, in a later sprint, the format-specific parsers. They live in the
domain layer because every parser must return a common structure and the
rest of the system must remain independent of the PDF library used.
"""

from dataclasses import dataclass

from app.domain.document_processing.enums import DocumentType, ExtractionStatus


@dataclass(frozen=True)
class TextElement:
    """A single word with its geometric position on the page.

    Positions (left, top, right, bottom in points) are preserved so parsers
    can interpret table columns positionally instead of guessing from values
    (ADR-002: identify the field/column before interpreting the value).
    """

    text: str
    x0: float
    top: float
    x1: float
    bottom: float


@dataclass(frozen=True)
class PageData:
    """Raw content of a single PDF page."""

    page_number: int
    text: str
    words: tuple[TextElement, ...] = ()
    status: ExtractionStatus = ExtractionStatus.NO_TEXT


@dataclass(frozen=True)
class RawDocumentData:
    """Raw content extracted from a PDF by a reader.

    This is the input for the document detector and, in a later sprint, for
    the format-specific parsers (ADR-002 flow).
    """

    filename: str
    pages: tuple[PageData, ...] = ()
    producer: str | None = None

    @property
    def page_count(self) -> int:
        """Number of pages in the document."""
        return len(self.pages)

    @property
    def full_text(self) -> str:
        """Full text of the document joining every page."""
        return "\n".join(page.text for page in self.pages)

    @property
    def status(self) -> ExtractionStatus:
        """Overall extraction status derived from the pages."""
        statuses = {page.status for page in self.pages}
        if not statuses:
            return ExtractionStatus.NO_TEXT
        if ExtractionStatus.EXTRACTED in statuses:
            return ExtractionStatus.EXTRACTED
        if ExtractionStatus.SCANNED_CANDIDATE in statuses:
            return ExtractionStatus.SCANNED_CANDIDATE
        return ExtractionStatus.NO_TEXT


@dataclass(frozen=True)
class DetectionResult:
    """Result of the document detector (ADR-002).

    Indicates the detected document structure and the parser that should be
    used to process it. A document is considered recognized when its type is
    not ``UNKNOWN``.
    """

    document_type: DocumentType
    parser_id: str
    confidence: float
    matched_signals: tuple[str, ...] = ()

    @property
    def is_recognized(self) -> bool:
        """Whether the document structure was recognized."""
        return self.document_type != DocumentType.UNKNOWN
