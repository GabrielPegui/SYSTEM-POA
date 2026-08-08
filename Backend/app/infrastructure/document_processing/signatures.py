"""Registry of document signatures for the known purchase order formats.

Each signature identifies a document structure by content signals extracted
from the real sample corpus (docs/samples). Signals are case-insensitive
substrings matched against the full extracted text. This is the extension
point: a new client format is registered here without touching the detector.
"""

from app.domain.document_processing.enums import DocumentType
from app.infrastructure.document_processing.detector import DocumentSignature

DEFAULT_SIGNATURES: tuple[DocumentSignature, ...] = (
    DocumentSignature(
        document_type=DocumentType.MERCADAL,
        parser_id="mercadal_parser",
        signals=(
            "pedido de compra",
            "comprado a:",
            "fecha creación",
            "fecha vencimiento",
            "cant. bultos",
        ),
    ),
    DocumentSignature(
        document_type=DocumentType.HILTON,
        parser_id="hilton_parser",
        signals=(
            "embassy suites",
            "precio/u",
            "silver sun gallery",
            "total orden",
        ),
    ),
    DocumentSignature(
        document_type=DocumentType.CDE_HYPER,
        parser_id="cde_hyper_parser",
        signals=(
            "hyper duarte",
            "pedido / order",
            "fecha de entrega imperativa",
            "n° artículo",
        ),
    ),
    DocumentSignature(
        document_type=DocumentType.JUMBO,
        parser_id="jumbo_parser",
        signals=(
            "jumbo higüey",
            "orden de pedido",
            "cantidad pedida",
            "esperamos su confirmación de pedido",
        ),
    ),
    DocumentSignature(
        document_type=DocumentType.BRAVO,
        parser_id="bravo_parser",
        signals=(
            "ctd.pedido",
            "prohibido dar o recibir",
            "entregar en: centro de distribución",
        ),
    ),
    DocumentSignature(
        document_type=DocumentType.PLAZA_LAMA,
        parser_id="plaza_lama_parser",
        signals=(
            "plaza lama",
            "pos. ii material",
            "dirección del proveedor",
            "valor neto por posicion",
        ),
    ),
)
