"""Process all 9 real sample PDFs through the full pipeline (Sprint 6).

Pipeline: PDF Reader -> Document Detector -> format-specific Parser.
The 2 scanned PDFs are reported as SCANNED (OCR is a future extension).
"""

from pathlib import Path

from app.domain.document_processing.exceptions import (
    DocumentProcessingError,
    PDFNoTextError,
    PDFReadError,
)
from app.infrastructure.document_processing.detector import DocumentDetector
from app.infrastructure.document_processing.parsers.registry import DEFAULT_PARSERS
from app.infrastructure.document_processing.reader import PdfplumberPDFReader
from app.infrastructure.document_processing.signatures import DEFAULT_SIGNATURES

SAMPLES_DIR = Path(__file__).resolve().parents[2] / "docs" / "samples"

reader = PdfplumberPDFReader()
detector = DocumentDetector(signatures=DEFAULT_SIGNATURES)

header = f"{'PDF':<45} {'Detector':<14} {'Parser':<18} {'Orden':<12} {'Items':<6} Resultado"
print(header)
print("-" * len(header))

for path in sorted(SAMPLES_DIR.glob("*")):
    if path.suffix.lower() != ".pdf":
        continue
    try:
        raw = reader.read(path)
        detection = detector.detect(raw)
        if not detection.is_recognized:
            print(f"{path.name:<45} {'-':<14} {'-':<18} {'-':<12} {'-':<6} NO RECONOCIDO")
            continue
        document = DEFAULT_PARSERS[detection.parser_id].parse(raw)
        print(
            f"{path.name:<45} {detection.document_type.value:<14} "
            f"{detection.parser_id:<18} {document.order_number:<12} "
            f"{len(document.items):<6} OK"
        )
    except PDFNoTextError:
        print(f"{path.name:<45} {'-':<14} {'-':<18} {'-':<12} {'-':<6} SCANNED (OCR futuro)")
    except (PDFReadError, DocumentProcessingError) as exc:
        print(f"{path.name:<45} {'-':<14} {'-':<18} {'-':<12} {'-':<6} ERROR: {exc}")
