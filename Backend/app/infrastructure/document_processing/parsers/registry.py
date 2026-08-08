"""Parser registry mapping parser ids to IPDFParser instances (ADR-002).

The registry is the extension point for new document formats: a new parser
is added here and referenced by the corresponding ``DocumentSignature``
(``parser_id``), keeping the detector and the pipeline unchanged.
"""

from app.domain.interfaces.pdf_parsers import IPDFParser
from app.infrastructure.document_processing.parsers.bravo import BravoParser
from app.infrastructure.document_processing.parsers.cde_hyper import CdeHyperParser
from app.infrastructure.document_processing.parsers.hilton import HiltonParser
from app.infrastructure.document_processing.parsers.jumbo import JumboParser
from app.infrastructure.document_processing.parsers.mercadal import MercadalParser
from app.infrastructure.document_processing.parsers.plaza_lama import PlazaLamaParser

DEFAULT_PARSERS: dict[str, IPDFParser] = {
    "mercadal_parser": MercadalParser(),
    "hilton_parser": HiltonParser(),
    "cde_hyper_parser": CdeHyperParser(),
    "jumbo_parser": JumboParser(),
    "bravo_parser": BravoParser(),
    "plaza_lama_parser": PlazaLamaParser(),
}


class ParserRegistry:
    """Registry of parsers keyed by their ``parser_id``."""

    def __init__(self, parsers: dict[str, IPDFParser] | None = None) -> None:
        self._parsers: dict[str, IPDFParser] = dict(parsers) if parsers else {}

    def register(self, parser_id: str, parser: IPDFParser) -> None:
        if not parser_id:
            raise ValueError("parser_id must not be empty")
        self._parsers[parser_id] = parser

    def get(self, parser_id: str) -> IPDFParser:
        if parser_id not in self._parsers:
            raise KeyError(f"Unknown parser id: {parser_id}")
        return self._parsers[parser_id]

    def __contains__(self, parser_id: str) -> bool:
        return parser_id in self._parsers

    @property
    def parser_ids(self) -> tuple[str, ...]:
        """Registered parser ids."""
        return tuple(self._parsers)

    @classmethod
    def with_defaults(cls) -> "ParserRegistry":
        """Build a registry preloaded with the default parsers."""
        return cls(DEFAULT_PARSERS)
