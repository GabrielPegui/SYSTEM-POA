"""Tests for the document detector using the real sample corpus."""

from pathlib import Path

import pytest

from app.domain.document_processing.enums import DocumentType
from app.domain.document_processing.models import DetectionResult, PageData, RawDocumentData
from app.infrastructure.document_processing.detector import DocumentDetector
from app.infrastructure.document_processing.reader import PdfplumberPDFReader
from app.infrastructure.document_processing.signatures import DEFAULT_SIGNATURES

EXPECTED_DOCUMENTS: tuple[tuple[str, DocumentType], ...] = (
    ("OLE(imagen).pdf", DocumentType.MERCADAL),
    ("mercadal.pdf", DocumentType.MERCADAL),
    ("OPERADORA WESTPARK, SAS.pdf", DocumentType.HILTON),
    ("carrefour.PDF", DocumentType.CDE_HYPER),
    ("Orden de Pedido por e-mail.pdf", DocumentType.JUMBO),
    ("bravo(imagen).pdf", DocumentType.BRAVO),
    ("plazalama.pdf", DocumentType.PLAZA_LAMA),
)


@pytest.mark.parametrize(
    ("filename", "expected_type"),
    EXPECTED_DOCUMENTS,
    ids=[filename for filename, _ in EXPECTED_DOCUMENTS],
)
def test_detector_recognizes_real_documents(
    reader: PdfplumberPDFReader,
    detector: DocumentDetector,
    samples_dir: Path,
    filename: str,
    expected_type: DocumentType,
) -> None:
    raw = reader.read(samples_dir / filename)
    result = detector.detect(raw)

    assert isinstance(result, DetectionResult)
    assert result.document_type == expected_type
    assert result.is_recognized
    assert result.confidence >= 0.6
    assert result.matched_signals


def test_detector_returns_unknown_for_unrelated_text(detector: DocumentDetector) -> None:
    raw = RawDocumentData(
        filename="unknown.txt",
        pages=(PageData(page_number=1, text="Factura de servicio sin estructura conocida"),),
    )

    result = detector.detect(raw)

    assert result.document_type == DocumentType.UNKNOWN
    assert not result.is_recognized
    assert result.parser_id == "unknown"
    assert result.confidence < 0.6


def test_detector_matches_signals_case_insensitively(detector: DocumentDetector) -> None:
    raw = RawDocumentData(
        filename="lowercase.txt",
        pages=(PageData(page_number=1, text="pedido de compra comprado a: fecha creación"),),
    )

    result = detector.detect(raw)

    assert result.document_type == DocumentType.MERCADAL


def test_registry_has_unique_document_types() -> None:
    types = [signature.document_type for signature in DEFAULT_SIGNATURES]
    assert len(types) == len(set(types))
