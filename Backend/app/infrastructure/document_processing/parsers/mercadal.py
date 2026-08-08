"""Parser for the Mercadal "Pedido de compra" format (ADR-002)."""

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
    find_date,
    first_decimal,
    first_quantity,
    line_text,
    tokens_in,
    words_in,
)


class MercadalParser(BaseParser):
    """Parses Mercadal purchase orders.

    Layout (verified against ``docs/samples/4000326734.pdf`` and
    ``4000326758.pdf``): the header carries the order number, creation and
    due dates; each item row has a 12-digit code, description, unit, price,
    quantity (``211.000`` means 211) and total. A 13-digit EAN is printed on
    the line right below each item. Section headers with 8-digit codes are
    ignored.
    """

    def _parse(self, raw_document: RawDocumentData) -> PurchaseOrderDocument:
        lines = self._lines(raw_document)
        order_number, order_date = self._order_header(lines)
        return PurchaseOrderDocument(
            order_number=order_number,
            items=tuple(self._items(lines)),
            customer_code=self._customer_code(lines),
            customer_name=self._customer_name(lines),
            order_date=order_date,
            delivery_date=self._delivery_date(lines),
            source_filename=raw_document.filename,
            document_type=DocumentType.MERCADAL,
        )

    def _order_header(self, lines: list[list[TextElement]]) -> tuple[str, date | None]:
        for index, line in enumerate(lines):
            if any(word.text.upper() == "NUMERO" for word in line):
                if index + 1 >= len(lines) or not lines[index + 1]:
                    break
                order_line = lines[index + 1]
                return order_line[0].text, find_date(order_line)
        raise DocumentProcessingError("MercadalParser: order header not found")

    def _delivery_date(self, lines: list[list[TextElement]]) -> date | None:
        for line in lines:
            if any("vencimiento" in word.text.lower() for word in line):
                return find_date(line)
        return None

    def _customer_code(self, lines: list[list[TextElement]]) -> str | None:
        for line in lines:
            for word in line:
                match = re.fullmatch(r"RNC-(\d+)", word.text, re.IGNORECASE)
                if match:
                    return match.group(1)
        return None

    def _customer_name(self, lines: list[list[TextElement]]) -> str | None:
        """Return the line printed right after the customer RNC.

        In the real samples this is the delivery account name (e.g. ``Mercadal
        Guaricanos``) or the delivery address (``Av. Duarte``); the matcher
        decides whether it is conclusive evidence.
        """
        for index, line in enumerate(lines):
            if not any(re.search(r"RNC-", word.text, re.IGNORECASE) for word in line):
                continue
            if index + 1 < len(lines) and lines[index + 1]:
                return line_text(lines[index + 1]).strip() or None
        return None

    def _items(self, lines: list[list[TextElement]]) -> list[PurchaseOrderItemDocument]:
        raw_items: list[dict] = []
        for line in lines:
            if not line:
                continue
            first = line[0].text
            if re.fullmatch(r"\d{12}", first):
                raw_items.append(self._item_fields(line))
            elif re.fullmatch(r"\d{13}", first) and raw_items and raw_items[-1]["ean"] is None:
                raw_items[-1]["ean"] = first
        return [PurchaseOrderItemDocument(**fields) for fields in raw_items]

    @staticmethod
    def _item_fields(line: list[TextElement]) -> dict:
        code = line[0].text
        quantity = first_quantity(tokens_in(line, 420, 480))
        if quantity is None:
            raise DocumentProcessingError(f"MercadalParser: missing quantity for item {code}")
        return {
            "pdf_code": code,
            "description": line_text(words_in(line, 88, 200)).strip(),
            "ean": None,
            "uom": line_text(words_in(line, 200, 240)).strip() or None,
            "unit_price": first_decimal(tokens_in(line, 300, 380)),
            "quantity": quantity,
            "total": first_decimal(tokens_in(line, 500, 580)),
        }
