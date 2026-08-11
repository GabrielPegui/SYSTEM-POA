"""Tests for the PDF reader abstraction and its pdfplumber implementation."""

from pathlib import Path

import pytest

from app.domain.document_processing.exceptions import PDFNoTextError, PDFReadError
from app.domain.document_processing.models import RawDocumentData
from app.infrastructure.document_processing.reader import PdfplumberPDFReader, PDFReader


def test_reader_is_abstract() -> None:
    with pytest.raises(TypeError):
        PDFReader()


def test_pdfplumber_reader_reads_text_pdf(reader: PdfplumberPDFReader, samples_dir: Path) -> None:
    raw = reader.read(samples_dir / "OLE.pdf")

    assert isinstance(raw, RawDocumentData)
    assert raw.filename == "OLE.pdf"
    assert raw.page_count == 1
    assert "Pedido de compra" in raw.full_text
    assert raw.producer is not None


def test_pdfplumber_reader_reads_multipage_pdf(reader: PdfplumberPDFReader, samples_dir: Path) -> None:
    raw = reader.read(samples_dir / "carrefour.PDF")

    assert raw.page_count == 2
    assert [page.page_number for page in raw.pages] == [1, 2]
    assert all(page.text.strip() for page in raw.pages)


def test_pdfplumber_reader_keeps_per_page_text(reader: PdfplumberPDFReader, samples_dir: Path) -> None:
    raw = reader.read(samples_dir / "plazalama.pdf")

    first, second = raw.pages
    assert "Plaza Lama" in first.text
    assert "Valor Bruto" in second.text


def test_pdfplumber_reader_keeps_positional_words(reader: PdfplumberPDFReader, samples_dir: Path) -> None:
    raw = reader.read(samples_dir / "BOLIN 4012234.pdf")

    page = raw.pages[0]
    assert page.words
    word = page.words[0]
    assert word.text
    assert word.x0 <= word.x1
    assert word.top <= word.bottom
    # Price evidence: 192.50 is Precio/U, not quantity (positional data kept).
    assert any("192.50" == w.text for w in page.words)


def test_pdfplumber_reader_raises_on_scanned_pdf(reader: PdfplumberPDFReader, samples_dir: Path) -> None:
    with pytest.raises(PDFNoTextError):
        reader.read(samples_dir / "imagen en pdf 1.pdf")


def test_pdfplumber_reader_raises_on_missing_file(reader: PdfplumberPDFReader, samples_dir: Path) -> None:
    with pytest.raises(PDFReadError):
        reader.read(samples_dir / "does-not-exist.pdf")
