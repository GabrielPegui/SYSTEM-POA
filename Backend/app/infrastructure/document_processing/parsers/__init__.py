"""Format-specific PDF parsers (ADR-002).

Every parser implements :class:`IPDFParser` and returns a normalized
``PurchaseOrderDocument``. Parsers only interpret the document structure;
they never contain business rules, never access repositories and never
match against the catalog (matching is a separate step handled by the
``CustomerMatcher``).
"""

from app.infrastructure.document_processing.parsers.base import BaseParser
from app.infrastructure.document_processing.parsers.bravo import BravoParser
from app.infrastructure.document_processing.parsers.cde_hyper import CdeHyperParser
from app.infrastructure.document_processing.parsers.hilton import HiltonParser
from app.infrastructure.document_processing.parsers.jumbo import JumboParser
from app.infrastructure.document_processing.parsers.mercadal import MercadalParser
from app.infrastructure.document_processing.parsers.plaza_lama import PlazaLamaParser
from app.infrastructure.document_processing.parsers.registry import (
    DEFAULT_PARSERS,
    ParserRegistry,
)

__all__ = [
    "BaseParser",
    "BravoParser",
    "CdeHyperParser",
    "DEFAULT_PARSERS",
    "HiltonParser",
    "JumboParser",
    "MercadalParser",
    "ParserRegistry",
    "PlazaLamaParser",
]
