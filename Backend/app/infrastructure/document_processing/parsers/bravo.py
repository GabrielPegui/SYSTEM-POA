"""Parser for the Bravo "Pedido" format (ADR-002)."""

import re
from datetime import date
from decimal import Decimal

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


class BravoParser(BaseParser):
    """Parses Bravo purchase orders (``docs/samples/pedido-03-08-2026-12653-bravo.pdf``).

    Layout: the order number and date sit on the "P/... / 31 Julio 2026" row
    and the delivery date on the "Fecha Entrega" row. Each item row has a
    position, code, description, EAN/UPC and quantity; the "Valor bruto" row
    below carries the unit cost and total value.
    """

    def _parse(self, raw_document: RawDocumentData) -> PurchaseOrderDocument:
        lines = self._lines(raw_document)
        order_number, order_date = self._header(lines)
        return PurchaseOrderDocument(
            order_number=order_number,
            items=tuple(self._items(lines)),
            order_date=order_date,
            delivery_date=self._delivery_date(lines),
            source_filename=raw_document.filename,
            document_type=DocumentType.BRAVO,
        )

    def _header(self, lines: list[list[TextElement]]) -> tuple[str, date | None]:
        for line in lines:
            for word in line:
                match = re.fullmatch(r"P/(\d+)", word.text)
                if match:
                    return match.group(1), find_date(line)
        raise DocumentProcessingError("BravoParser: order header not found")

    def _delivery_date(self, lines: list[list[TextElement]]) -> date | None:
        for line in lines:
            if not any(word.text.lower() == "entrega" for word in line):
                continue
            found = find_date(line)
            if found is not None:
                return found
        return None

    def _items(self, lines: list[list[TextElement]]) -> list[PurchaseOrderItemDocument]:
        items: list[PurchaseOrderItemDocument] = []
        for index, line in enumerate(lines):
            if not self._is_item_line(line):
                continue
            code = self._code(line)
            quantity = first_quantity(tokens_in(line, 410, 445))
            if quantity is None:
                raise DocumentProcessingError(f"BravoParser: missing quantity for item {code}")
            unit_price, total = self._price_total(lines, index)
            items.append(
                PurchaseOrderItemDocument(
                    pdf_code=code,
                    ean=self._ean(line),
                    description=line_text(words_in(line, 80, 298)).strip(),
                    uom=line_text(words_in(line, 445, 468)).strip() or None,
                    unit_price=unit_price,
                    quantity=quantity,
                    total=total,
                    line_number=int(line[0].text),
                )
            )
        return items

    @staticmethod
    def _is_item_line(line: list[TextElement]) -> bool:
        if not line or not re.fullmatch(r"\d{1,2}", line[0].text):
            return False
        if not any(re.fullmatch(r"\d{4,6}", word.text) and 35 <= word.x0 < 75 for word in line):
            return False
        return any(re.fullmatch(r"\d{13}", word.text) and 298 <= word.x0 < 380 for word in line)

    @staticmethod
    def _code(line: list[TextElement]) -> str:
        for word in line:
            if re.fullmatch(r"\d{4,6}", word.text) and 35 <= word.x0 < 75:
                return word.text
        raise DocumentProcessingError("BravoParser: item code not found")

    @staticmethod
    def _ean(line: list[TextElement]) -> str | None:
        for word in line:
            if re.fullmatch(r"\d{13}", word.text) and 298 <= word.x0 < 380:
                return word.text
        return None

    @staticmethod
    def _price_total(
        lines: list[list[TextElement]], index: int
    ) -> tuple[Decimal | None, Decimal | None]:
        for i in range(index + 1, min(index + 7, len(lines))):
            if not any(word.text.lower() == "bruto" for word in lines[i]):
                continue
            unit_price = first_decimal(tokens_in(lines[i], 400, 445))
            total = first_decimal(tokens_in(lines[i], 500, 560))
            for line in lines[i + 1 : i + 3]:
                unit_price = unit_price or first_decimal(tokens_in(line, 400, 445))
                total = total or first_decimal(tokens_in(line, 500, 560))
                if unit_price is not None and total is not None:
                    break
            return unit_price, total
        return None, None
