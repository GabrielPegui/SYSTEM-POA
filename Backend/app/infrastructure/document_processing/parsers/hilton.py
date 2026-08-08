"""Parser for the Hilton "Orden de Compra" format (ADR-002)."""

import re
from datetime import date

from app.domain.document_processing.enums import DocumentType
from app.domain.document_processing.exceptions import DocumentProcessingError
from app.domain.document_processing.models import RawDocumentData, TextElement
from app.domain.document_processing.purchase_order import (
    PurchaseOrderDocument,
    PurchaseOrderItemDocument,
)
from app.infrastructure.document_processing.parsers.base import (
    BaseParser,
    first_decimal,
    first_quantity,
    line_text,
    parse_date,
    tokens_in,
    words_in,
)


class HiltonParser(BaseParser):
    """Parses Hilton purchase orders (``docs/samples/BOLIN 4012234.pdf``).

    Layout: the order number is a standalone numeric line at the top; the
    "Fecha / Términos / Fecha Entrega" header row carries the order and
    delivery dates; each item row has quantity, a bracketed material code
    (``[OWP...]``), description, unit code, unit price and total. The
    customer RNC is printed next to an ``RNC:`` label.
    """

    def _parse(self, raw_document: RawDocumentData) -> PurchaseOrderDocument:
        lines = self._lines(raw_document)
        order_date, delivery_date = self._dates(lines)
        return PurchaseOrderDocument(
            order_number=self._order_number(lines),
            items=tuple(self._items(lines)),
            customer_code=self._customer_code(lines),
            customer_name=self._customer_name(lines),
            order_date=order_date,
            delivery_date=delivery_date,
            source_filename=raw_document.filename,
            document_type=DocumentType.HILTON,
        )

    def _order_number(self, lines: list[list[TextElement]]) -> str:
        for line in lines:
            text = line_text(line)
            if re.fullmatch(r"\d{5,10}", text):
                return text
        raise DocumentProcessingError("HiltonParser: order number not found")

    def _dates(self, lines: list[list[TextElement]]) -> tuple[date | None, date | None]:
        for line in lines:
            if not any(word.text.lower() == "dias" for word in line):
                continue
            dates = [parsed for parsed in (parse_date(word.text) for word in line) if parsed is not None]
            order_date = dates[0] if dates else None
            delivery_date = dates[1] if len(dates) > 1 else None
            return order_date, delivery_date
        return None, None

    def _customer_code(self, lines: list[list[TextElement]]) -> str | None:
        words = [word for line in lines for word in line]
        rnc_label = next((word for word in words if word.text.upper().startswith("RNC")), None)
        if rnc_label is None:
            return None
        for word in words:
            if re.fullmatch(r"\d{9}", word.text) and abs(word.top - rnc_label.top) <= 3:
                return word.text
        return None

    def _customer_name(self, lines: list[list[TextElement]]) -> str | None:
        """Return the account name on the line right below ``Ordenado a:``.

        Verified against ``docs/samples/BOLIN 4012234.pdf``: the header
        ``Ordenado a: Enviar a:`` is followed by ``EMBASSY SUITES HOTEL (OWP)``.
        """
        for index, line in enumerate(lines):
            if not any(word.text.upper().startswith("ORDENADO") for word in line):
                continue
            if index + 1 < len(lines) and lines[index + 1]:
                return line_text(lines[index + 1]).strip() or None
        return None

    def _items(self, lines: list[list[TextElement]]) -> list[PurchaseOrderItemDocument]:
        items: list[PurchaseOrderItemDocument] = []
        for line in lines:
            if not self._is_item_line(line):
                continue
            code = self._code(line)
            quantity = first_quantity(tokens_in(line, 0, 60))
            if quantity is None:
                raise DocumentProcessingError(f"HiltonParser: missing quantity for item {code}")
            items.append(
                PurchaseOrderItemDocument(
                    pdf_code=code,
                    description=line_text(words_in(line, 150, 245)).strip(),
                    uom=line_text(words_in(line, 245, 372)).strip() or None,
                    unit_price=first_decimal(tokens_in(line, 400, 460)),
                    quantity=quantity,
                    total=first_decimal(tokens_in(line, 540, 580)),
                )
            )
        return items

    @staticmethod
    def _is_item_line(line: list[TextElement]) -> bool:
        return any(re.fullmatch(r"\[[A-Z0-9]+\]", word.text) for word in line)

    @staticmethod
    def _code(line: list[TextElement]) -> str:
        for word in line:
            match = re.fullmatch(r"\[([A-Z0-9]+)\]", word.text)
            if match:
                return match.group(1)
        raise DocumentProcessingError("HiltonParser: item code not found")
