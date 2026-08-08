"""Document detector based on content signals (ADR-002).

The detector inspects the raw document data and decides which parser should
handle the document. Detection is content-based (headings, keywords,
patterns), never filename-based, and it is extensible: each document
structure registers a set of signals instead of hard-coding ``if client``
logic.
"""

from dataclasses import dataclass

from app.domain.document_processing.enums import DocumentType
from app.domain.document_processing.models import DetectionResult, RawDocumentData


@dataclass(frozen=True)
class DocumentSignature:
    """A set of content signals identifying a document structure.

    A document scores against every signal (case-insensitive substring in the
    full text). The best signature wins when its confidence is at least the
    configured threshold.
    """

    document_type: DocumentType
    parser_id: str
    signals: tuple[str, ...]


class DocumentDetector:
    """Detects the document structure using a registry of signatures.

    The registry is the single extensibility point: adding a new client
    format only requires registering a new :class:`DocumentSignature`; the
    detector logic itself stays unchanged.
    """

    def __init__(self, signatures: tuple[DocumentSignature, ...], min_confidence: float = 0.6) -> None:
        if not signatures:
            raise ValueError("At least one document signature is required")
        self._signatures = signatures
        self._min_confidence = min_confidence

    def detect(self, raw_document: RawDocumentData) -> DetectionResult:
        full_text = raw_document.full_text.lower()
        best: tuple[float, DocumentSignature, tuple[str, ...]] | None = None
        for signature in self._signatures:
            matched = tuple(signal for signal in signature.signals if signal in full_text)
            confidence = len(matched) / len(signature.signals)
            if best is None or confidence > best[0]:
                best = (confidence, signature, matched)

        assert best is not None
        confidence, signature, matched = best
        if confidence < self._min_confidence:
            return DetectionResult(
                document_type=DocumentType.UNKNOWN,
                parser_id="unknown",
                confidence=confidence,
                matched_signals=matched,
            )
        return DetectionResult(
            document_type=signature.document_type,
            parser_id=signature.parser_id,
            confidence=confidence,
            matched_signals=matched,
        )
