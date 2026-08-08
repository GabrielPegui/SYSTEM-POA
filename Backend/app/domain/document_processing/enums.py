"""Enums for document processing (ADR-002)."""

import enum


class ExtractionStatus(enum.Enum):
    """Extraction state of a page or document.

    - ``EXTRACTED``: text was extracted successfully.
    - ``SCANNED_CANDIDATE``: no text found but the page contains images
      (likely a scanned document; OCR is a future extension).
    - ``NO_TEXT``: no text and no images; nothing to process.
    """

    EXTRACTED = "extracted"
    SCANNED_CANDIDATE = "scanned_candidate"
    NO_TEXT = "no_text"


class DocumentType(enum.Enum):
    """Known document structures detected by the DocumentDetector.

    Values follow the formats identified in the sample corpus (ADR-002).
    ``UNKNOWN`` is used when no registered signature matches, meaning the
    document requires manual review or a future OCR pass.
    """

    UNKNOWN = "unknown"
    MERCADAL = "mercadal"
    HILTON = "hilton"
    CDE_HYPER = "cde_hyper"
    JUMBO = "jumbo"
    BRAVO = "bravo"
    PLAZA_LAMA = "plaza_lama"
