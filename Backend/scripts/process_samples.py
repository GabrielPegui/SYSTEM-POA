"""Process all 9 real sample PDFs and print the detection report (Sprint 5)."""

from pathlib import Path

from app.domain.document_processing.exceptions import PDFNoTextError, PDFReadError
from app.infrastructure.document_processing.detector import DocumentDetector
from app.infrastructure.document_processing.reader import PdfplumberPDFReader
from app.infrastructure.document_processing.signatures import DEFAULT_SIGNATURES

SAMPLES_DIR = Path(__file__).resolve().parents[2] / "docs" / "samples"

reader = PdfplumberPDFReader()
detector = DocumentDetector(signatures=DEFAULT_SIGNATURES)

header = f"{'PDF':<45} {'Texto':<8} {'Pags':<5} {'Detector':<14} {'Conf':<6} Resultado"
print(header)
print("-" * len(header))

for path in sorted(SAMPLES_DIR.glob("*")):
    if path.suffix.lower() not in {".pdf"}:
        continue
    try:
        raw = reader.read(path)
        result = detector.detect(raw)
        texto = "SI" if raw.status.value == "extracted" else "NO"
        print(
            f"{path.name:<45} {texto:<8} {raw.page_count:<5} "
            f"{result.document_type.value:<14} {result.confidence:<6.2f} OK"
        )
    except PDFNoTextError:
        print(f"{path.name:<45} {'NO':<8} {'-':<5} {'-':<14} {'-':<6} SCANNED (OCR futuro)")
    except PDFReadError as exc:
        print(f"{path.name:<45} {'-':<8} {'-':<5} {'-':<14} {'-':<6} ERROR: {exc}")
