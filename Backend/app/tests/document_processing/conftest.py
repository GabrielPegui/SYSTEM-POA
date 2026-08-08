"""Shared fixtures for document processing tests.

The samples are the real PDFs committed under ``docs/samples`` (outside the
Backend folder), resolved from the repository root so tests exercise the
reader and detector against the actual document corpus.
"""

from pathlib import Path

import pytest

from app.infrastructure.document_processing.detector import DocumentDetector
from app.infrastructure.document_processing.reader import PdfplumberPDFReader
from app.infrastructure.document_processing.signatures import DEFAULT_SIGNATURES

REPO_ROOT = Path(__file__).resolve().parents[4]
SAMPLES_DIR = REPO_ROOT / "docs" / "samples"


@pytest.fixture
def reader() -> PdfplumberPDFReader:
    return PdfplumberPDFReader()


@pytest.fixture
def detector() -> DocumentDetector:
    return DocumentDetector(signatures=DEFAULT_SIGNATURES)


@pytest.fixture
def samples_dir() -> Path:
    return SAMPLES_DIR
