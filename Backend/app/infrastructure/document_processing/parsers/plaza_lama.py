"""Parser for the Plaza Lama "Orden de Compra" format (ADR-002)."""

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


class PlazaLamaParser(BaseParser):
    """Parses Plaza Lama purchase orders (``docs/samples/Orden de Compra 4505261004.pdf``).

    Layout (2 pages): the "Pedido / Fecha" row carries the order number and
    order date; the "Fecha de Entrega" row carries the delivery date. Each
    item row has position, material code, EAN, quantity, unit, unit price
    and total; the description is printed on the line right below.
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
            document_type=DocumentType.PLAZA_LAMA,
        )

    def _header(self, lines: list[list[TextElement]]) -> tuple[str, date | None]:
        for line in lines:
            if not any(word.text.lower() == "pedido" for word in line):
                continue
            number = next((word.text for word in line if re.fullmatch(r"\d{10}", word.text)), None)
            if number is None:
                continue
            return number, find_date(line)
        raise DocumentProcessingError("PlazaLamaParser: order header not found")

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
        """Return the store name on the first line carrying ``Plaza Lama``.

        Verified against ``docs/samples/Orden de Compra 4505261004.pdf``: the
        delivery section prints ``Plaza Lama Santiago`` on its own line.
        """
        for line in lines:
            if not any(word.text.upper() == "PLAZA" for word in line):
                continue
            if not any(word.text.upper() == "LAMA" for word in line):
                continue
            return line_text(line).strip() or None
        return None

    def _items(self, lines: list[list[TextElement]]) -> list[PurchaseOrderItemDocument]:
        items: list[PurchaseOrderItemDocument] = []
        for index, line in enumerate(lines):
            if not self._is_item_line(line):
                continue
            code = self._code(line)
            quantity = first_quantity(tokens_in(line, 320, 380))
            if quantity is None:
                raise DocumentProcessingError(f"PlazaLamaParser: missing quantity for item {code}")
            description = self._description(lines, index)
            if not description:
                raise DocumentProcessingError(f"PlazaLamaParser: missing description for item {code}")
            items.append(
                PurchaseOrderItemDocument(
                    pdf_code=code,
                    ean=self._ean(line),
                    description=description,
                    uom=line_text(words_in(line, 380, 445)).strip() or None,
                    unit_price=first_decimal(tokens_in(line, 440, 495)),
                    quantity=quantity,
                    total=first_decimal(tokens_in(line, 500, 570)),
                    line_number=int(line[0].text),
                )
            )
        return items

    @staticmethod
    def _is_item_line(line: list[TextElement]) -> bool:
        if not line or not re.fullmatch(r"\d{1,3}", line[0].text):
            return False
        if not any(re.fullmatch(r"\d{6,7}", word.text) and 55 <= word.x0 < 95 for word in line):
            return False
        return any(re.fullmatch(r"\d{13}", word.text) and 95 <= word.x0 < 240 for word in line)

    @staticmethod
    def _code(line: list[TextElement]) -> str:
        for word in line:
            if re.fullmatch(r"\d{6,7}", word.text) and 55 <= word.x0 < 95:
                return word.text
        raise DocumentProcessingError("PlazaLamaParser: item code not found")

    @staticmethod
    def _ean(line: list[TextElement]) -> str | None:
        for word in line:
            if re.fullmatch(r"\d{13}", word.text) and 95 <= word.x0 < 240:
                return word.text
        return None

    @staticmethod
    def _description(lines: list[list[TextElement]], index: int) -> str:
        if index + 1 >= len(lines):
            return ""
        return line_text(words_in(lines[index + 1], 55, 300)).strip()
