"""Parser for the CDE / Hyper "Pedido / Order" format (ADR-002)."""

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
    parse_date,
    tokens_in,
    words_in,
)


class CdeHyperParser(BaseParser):
    """Parses CDE / Hyper purchase orders.

    Layout (verified against ``docs/samples/CDE_1_2069_20260801075602_2.PDF``,
    2 pages): the "Fecha de pedido" row carries the order number and order
    date; "Fecha de entrega imperativa" carries the delivery date. Each item
    row has an article number, a 13-digit EAN, description, unit count and
    net purchase price. Some descriptions wrap to the line right below the
    item row. Multi-page documents produce a single document with all items.
    """

    def _parse(self, raw_document: RawDocumentData) -> PurchaseOrderDocument:
        lines = self._lines(raw_document)
        order_number, order_date = self._header(lines)
        return PurchaseOrderDocument(
            order_number=order_number,
            items=tuple(self._items(lines)),
            customer_code=self._customer_code(lines),
            customer_name=self._customer_name(lines),
            order_date=order_date,
            delivery_date=self._delivery_date(lines),
            source_filename=raw_document.filename,
            document_type=DocumentType.CDE_HYPER,
        )

    def _header(self, lines: list[list[TextElement]]) -> tuple[str, date | None]:
        for line in lines:
            if not any(word.text.lower() == "pedido" for word in line):
                continue
            number = next((word.text for word in line if re.fullmatch(r"\d{5,8}", word.text)), None)
            if number is None:
                continue
            return number, find_date(line)
        raise DocumentProcessingError("CdeHyperParser: order header not found")

    def _delivery_date(self, lines: list[list[TextElement]]) -> date | None:
        for line in lines:
            if not any(word.text.lower() == "entrega" for word in line):
                continue
            found = find_date(line)
            if found is not None:
                return found
        return None

    def _customer_code(self, lines: list[list[TextElement]]) -> str | None:
        for line in lines:
            for index, word in enumerate(line):
                if not word.text.upper().startswith("RNC"):
                    continue
                for other in line[index + 1 :]:
                    if re.fullmatch(r"\d{6,9}", other.text):
                        return other.text
        return None

    def _customer_name(self, lines: list[list[TextElement]]) -> str | None:
        """Return the merchant name on the first ``HYPER …`` line.

        Verified against ``docs/samples/CDE_1_2069_20260801075602_2.PDF``: the
        header ``HYPER DUARTE 01/08/2026 07:56`` carries the store name before
        the date. The matcher maps ``HYPER`` to the ``CARREFOUR`` chain.
        """
        for line in lines:
            if not any(word.text.upper() == "HYPER" for word in line):
                continue
            tokens = []
            for word in line:
                if parse_date(word.text) is not None:
                    break
                tokens.append(word.text)
            return " ".join(tokens).strip() or None
        return None

    def _items(self, lines: list[list[TextElement]]) -> list[PurchaseOrderItemDocument]:
        items: list[PurchaseOrderItemDocument] = []
        for index, line in enumerate(lines):
            if not self._is_item_line(line):
                continue
            code = line[0].text
            quantity = first_quantity(tokens_in(line, 370, 395))
            if quantity is None:
                raise DocumentProcessingError(f"CdeHyperParser: missing quantity for item {code}")
            description = self._description(lines, index)
            if not description:
                raise DocumentProcessingError(f"CdeHyperParser: missing description for item {code}")
            items.append(
                PurchaseOrderItemDocument(
                    pdf_code=code,
                    ean=self._ean(line),
                    description=description,
                    unit_price=first_decimal(tokens_in(line, 460, 500)),
                    quantity=quantity,
                )
            )
        return items

    @staticmethod
    def _is_item_line(line: list[TextElement]) -> bool:
        if not line or not re.fullmatch(r"\d{4,8}", line[0].text):
            return False
        return any(re.fullmatch(r"\d{13}", word.text) for word in line)

    @staticmethod
    def _ean(line: list[TextElement]) -> str | None:
        for word in line:
            if re.fullmatch(r"\d{13}", word.text):
                return word.text
        return None

    @staticmethod
    def _description(lines: list[list[TextElement]], index: int) -> str:
        description = line_text(words_in(lines[index], 160, 340)).strip()
        if description:
            return description
        if index + 1 < len(lines):
            next_line = lines[index + 1]
            if not CdeHyperParser._is_item_line(next_line):
                return line_text(words_in(next_line, 160, 340)).strip()
        return ""
