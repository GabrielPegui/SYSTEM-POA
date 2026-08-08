"""Parser for the Jumbo "Orden de Pedido" format (ADR-002)."""

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


class JumboParser(BaseParser):
    """Parses Jumbo purchase orders (``docs/samples/Orden de Pedido por e-mail.pdf``).

    Layout: the order number is a standalone 10-digit line; the order date
    sits on the address line and the delivery date on the "Fecha de entrega"
    row. Each item block starts with a position/material/EAN/quantity row,
    followed by a "Precio bruto" row holding the unit price and total.
    """

    def _parse(self, raw_document: RawDocumentData) -> PurchaseOrderDocument:
        lines = self._lines(raw_document)
        return PurchaseOrderDocument(
            order_number=self._order_number(lines),
            items=tuple(self._items(lines)),
            customer_code=self._customer_code(lines),
            customer_name=self._customer_name(lines),
            order_date=self._order_date(lines),
            delivery_date=self._delivery_date(lines),
            source_filename=raw_document.filename,
            document_type=DocumentType.JUMBO,
        )

    def _order_number(self, lines: list[list[TextElement]]) -> str:
        for line in lines:
            text = line_text(line)
            if re.fullmatch(r"\d{10}", text):
                return text
        raise DocumentProcessingError("JumboParser: order number not found")

    def _order_date(self, lines: list[list[TextElement]]) -> date | None:
        for line in lines:
            if any(word.text.upper().startswith("IND.HERRERA") for word in line):
                return find_date(line)
        return None

    def _delivery_date(self, lines: list[list[TextElement]]) -> date | None:
        for line in lines:
            if any(word.text.lower() == "entrega" for word in line):
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
                    if re.fullmatch(r"[\d-]{8,}", other.text):
                        return other.text
        return None

    def _customer_name(self, lines: list[list[TextElement]]) -> str | None:
        """Return the store name at the start of the first ``Jumbo …`` line.

        Verified against ``docs/samples/Orden de Pedido por e-mail.pdf``: the
        line ``Jumbo Higüey Almacén destino TDA1`` identifies the store before
        the ``Almacén`` keyword.
        """
        for line in lines:
            if not line or line[0].text.upper() != "JUMBO":
                continue
            tokens = []
            for word in line:
                if word.text.lower().startswith("almac"):
                    break
                tokens.append(word.text)
            return " ".join(tokens).strip() or None
        return None

    def _items(self, lines: list[list[TextElement]]) -> list[PurchaseOrderItemDocument]:
        items: list[PurchaseOrderItemDocument] = []
        for index, line in enumerate(lines):
            if not self._is_item_line(line):
                continue
            code = self._code(line)
            quantity = first_quantity(tokens_in(line, 350, 420))
            if quantity is None:
                raise DocumentProcessingError(f"JumboParser: missing quantity for item {code}")
            unit_price, total = self._price_total(lines, index)
            items.append(
                PurchaseOrderItemDocument(
                    pdf_code=code,
                    ean=self._ean(line),
                    description=line_text(words_in(line, 55, 260)).strip(),
                    uom=line_text(words_in(line, 260, 298)).strip() or None,
                    unit_price=unit_price,
                    quantity=quantity,
                    total=total,
                    line_number=int(line[0].text),
                )
            )
        return items

    @staticmethod
    def _is_item_line(line: list[TextElement]) -> bool:
        if not line or not re.fullmatch(r"\d{4}", line[0].text):
            return False
        if not any(re.fullmatch(r"\d{5,8}", word.text) and 25 <= word.x0 < 60 for word in line):
            return False
        return any(re.fullmatch(r"\d{13}", word.text) and 290 <= word.x0 < 340 for word in line)

    @staticmethod
    def _code(line: list[TextElement]) -> str:
        for word in line:
            if re.fullmatch(r"\d{5,8}", word.text) and 25 <= word.x0 < 60:
                return word.text
        raise DocumentProcessingError("JumboParser: item code not found")

    @staticmethod
    def _ean(line: list[TextElement]) -> str | None:
        for word in line:
            if re.fullmatch(r"\d{13}", word.text) and 290 <= word.x0 < 340:
                return word.text
        return None

    @staticmethod
    def _price_total(
        lines: list[list[TextElement]], index: int
    ) -> tuple[Decimal | None, Decimal | None]:
        for line in lines[index + 1 : index + 5]:
            if any(word.text.lower() == "bruto" for word in line):
                return (
                    first_decimal(tokens_in(line, 200, 285)),
                    first_decimal(tokens_in(line, 430, 480)),
                )
        return None, None
