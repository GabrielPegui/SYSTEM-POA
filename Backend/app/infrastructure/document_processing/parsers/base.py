"""Shared helpers for format-specific PDF parsers (ADR-002).

Parsers interpret the positional word data produced by the PDF reader.
This module centralizes value conversions (dates, quantities, decimals)
and the line-grouping logic so every parser stays focused on its own
document structure.
"""

import re
from abc import ABC, abstractmethod
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from app.domain.document_processing.models import RawDocumentData, TextElement
from app.domain.document_processing.purchase_order import PurchaseOrderDocument
from app.domain.interfaces.pdf_parsers import IPDFParser

_SPANISH_MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


def group_lines(words: tuple[TextElement, ...]) -> list[list[TextElement]]:
    """Group words into visual lines using their vertical position."""
    buckets: dict[float, list[TextElement]] = {}
    for word in words:
        buckets.setdefault(round(word.top, 1), []).append(word)
    lines = [sorted(bucket, key=lambda w: w.x0) for _, bucket in sorted(buckets.items())]
    return lines


def line_text(line: list[TextElement]) -> str:
    """Join a line's words into a single string."""
    return " ".join(word.text for word in line)


def tokens_in(line: list[TextElement], x0: float, x1: float) -> list[str]:
    """Return the texts of words whose left edge falls in [x0, x1)."""
    return [word.text for word in line if x0 <= word.x0 < x1]


def words_in(line: list[TextElement], x0: float, x1: float) -> list[TextElement]:
    """Return the words whose left edge falls in [x0, x1)."""
    return [word for word in line if x0 <= word.x0 < x1]


def parse_decimal(text: str) -> Decimal | None:
    """Parse a monetary value such as ``17,302.00`` into a Decimal."""
    try:
        return Decimal(text.replace(",", "").strip())
    except InvalidOperation:
        return None


def parse_quantity(text: str) -> int | None:
    """Parse a printed quantity such as ``211.000`` or ``10.00`` into an int."""
    digits = re.sub(r"[^0-9]", "", text.split(".")[0])
    if not digits:
        return None
    return int(digits)


def parse_date(text: str) -> date | None:
    """Parse common printed date formats including Spanish month names."""
    cleaned = text.strip()
    for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    match = re.fullmatch(r"(\d{1,2})\s+([A-Za-zÁ-ÿ]+)\s+(\d{4})", cleaned)
    if match:
        day, month_name, year = match.groups()
        month = _SPANISH_MONTHS.get(month_name.lower())
        if month:
            try:
                return date(int(year), month, int(day))
            except ValueError:
                return None
    return None


def first_decimal(values: list[str]) -> Decimal | None:
    """Return the first value that parses as a Decimal."""
    for value in values:
        parsed = parse_decimal(value)
        if parsed is not None:
            return parsed
    return None


def find_date(line: list[TextElement]) -> date | None:
    """Return the first date found on a line.

    Dates may be a single token (``03.08.2026``) or split across Spanish
    month words (``31 Julio 2026``).
    """
    tokens = [word.text for word in line]
    for token in tokens:
        parsed = parse_date(token)
        if parsed is not None:
            return parsed
    for index, token in enumerate(tokens):
        month = _SPANISH_MONTHS.get(token.lower())
        if not month:
            continue
        if index > 0 and index + 1 < len(tokens):
            try:
                return date(int(tokens[index + 1]), month, int(tokens[index - 1]))
            except ValueError:
                continue
    return None


def first_quantity(values: list[str]) -> int | None:
    """Return the first value that parses as a quantity."""
    for value in values:
        parsed = parse_quantity(value)
        if parsed is not None:
            return parsed
    return None


def all_page_lines(raw_document: RawDocumentData) -> list[list[TextElement]]:
    """Flatten every page's visual lines preserving reading order."""
    lines: list[list[TextElement]] = []
    for page in raw_document.pages:
        lines.extend(group_lines(page.words))
    return lines


class BaseParser(IPDFParser, ABC):
    """Shared scaffold for format-specific parsers (ADR-002).

    Concrete parsers implement ``_parse`` and reuse the module-level helpers
    for line grouping and value conversion.
    """

    def parse(self, raw_document: RawDocumentData) -> PurchaseOrderDocument:
        return self._parse(raw_document)

    @abstractmethod
    def _parse(self, raw_document: RawDocumentData) -> PurchaseOrderDocument:
        """Extract the standard document from the raw input."""

    @staticmethod
    def _lines(raw_document: RawDocumentData) -> list[list[TextElement]]:
        return all_page_lines(raw_document)
