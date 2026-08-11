"""Seed the definitive customer/route catalog from the source workbook.

Reads ``docs/data/CLIENTES POR RUTA.xlsx`` (columns ``RUTA``, ``CLIENTES``,
``DIRECCION``) and reconciles the catalog in the configured database so it
matches the workbook exactly (the workbook is the source of truth):

- Every route code in the workbook becomes a ``routes`` row (created when
  missing).
- Every ``(route, customer name)`` becomes a ``customers`` row. When a name
  is re-homed to a different route its ``route_id`` is updated in place (so
  orders that reference it keep their foreign key). Addresses are refreshed
  when the workbook provides one.
- Customers and routes that are no longer in the workbook are removed.
  Customers still referenced by orders are never deleted; they are kept and
  reported as a warning. The persistent uniqueness rule is
  ``(route_id, name)`` (the same name may exist on more than one route).

Usage:
    python scripts/seed_catalog.py [--path <xlsx>]

Exit code is 0 on success; duplicates (a name on more than one route) are
reported but do not fail the seed (they are valid catalog entries handled by
the matcher as REVIEW_REQUIRED).
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.database.base import Base
from app.database.session import get_engine
from app.infrastructure.persistence import models  # noqa: F401 (register tables on Base)
from app.infrastructure.persistence.models import (
    CustomerModel,
    OrderModel,
    RouteModel,
)

logger = get_logger(__name__)

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "docs" / "data" / "CLIENTES POR RUTA.xlsx"


def _load_rows(path: Path) -> list[tuple[str, str, str | None]]:
    """Read (route_code, customer_name, address) rows from the workbook."""
    import openpyxl

    workbook = openpyxl.load_workbook(path, data_only=True)
    sheet = workbook.active
    rows: list[tuple[str, str, str | None]] = []
    for index, row in enumerate(sheet.iter_rows(values_only=True)):
        if index == 0:
            continue
        route_code = str(row[0]).strip() if row[0] is not None else ""
        name = str(row[1]).strip() if row[1] is not None else ""
        if not route_code or not name:
            continue
        address = str(row[2]).strip() if len(row) > 2 and row[2] is not None else None
        rows.append((route_code, name, address))
    return rows


def _upsert_route(db: Session, code: str) -> RouteModel:
    model = db.scalars(select(RouteModel).where(RouteModel.code == code)).first()
    if model is None:
        model = RouteModel(code=code, name=code)
        db.add(model)
        db.flush()
    return model


def _reconcile(db: Session, rows: list[tuple[str, str, str | None]]) -> None:
    """Make the persisted catalog match the workbook (source of truth)."""
    route_by_code: dict[str, RouteModel] = {}
    for code, _, _ in rows:
        if code not in route_by_code:
            route_by_code[code] = _upsert_route(db, code)
    db.flush()
    route_id_by_code = {code: route.id for code, route in route_by_code.items()}

    targets_by_name: dict[str, list[tuple[int, str | None]]] = defaultdict(list)
    target_pairs: set[tuple[int, str]] = set()
    for code, name, address in rows:
        route_id = route_id_by_code[code]
        targets_by_name[name].append((route_id, address))
        target_pairs.add((route_id, name))

    by_name: dict[str, list[CustomerModel]] = defaultdict(list)
    for customer in db.scalars(select(CustomerModel)).all():
        by_name[customer.name].append(customer)

    needed_routes = {
        name: {route_id for route_id, _ in targets}
        for name, targets in targets_by_name.items()
    }
    present = {
        (customer.route_id, customer.name): customer
        for customers in by_name.values()
        for customer in customers
    }

    for name, targets in targets_by_name.items():
        for route_id, address in targets:
            customer = present.get((route_id, name))
            if customer is None:
                movable = next(
                    (
                        candidate
                        for candidate in by_name.get(name, [])
                        if candidate.route_id != route_id
                        and candidate.route_id not in needed_routes[name]
                    ),
                    None,
                )
                if movable is not None:
                    customer = movable
                    customer.route_id = route_id
                else:
                    customer = CustomerModel(route_id=route_id, name=name)
                    db.add(customer)
                present[(route_id, name)] = customer
            if address is not None and customer.address != address:
                customer.address = address
    db.flush()

    order_customer_ids = set(db.scalars(select(OrderModel.customer_id)).all())
    kept_for_orders: list[tuple[str, int]] = []
    for (route_id, name), customer in list(present.items()):
        if (route_id, name) in target_pairs:
            continue
        if customer.route_id != route_id:
            continue  # stale key pointing at a re-homed customer
        if customer.id in order_customer_ids:
            kept_for_orders.append((name, customer.id))
            continue
        db.delete(customer)
    if kept_for_orders:
        logger.warning(
            "Kept customers referenced by orders even though absent from the workbook: %s",
            ", ".join(f"{name} (id={customer_id})" for name, customer_id in kept_for_orders),
        )

    db.flush()
    for route in db.scalars(select(RouteModel)).all():
        if route.code not in route_id_by_code and not db.scalars(
            select(CustomerModel).where(CustomerModel.route_id == route.id).limit(1)
        ).first():
            db.delete(route)
    db.commit()


def seed(path: Path) -> None:
    """Reconcile routes and customers with the workbook."""
    engine = get_engine()
    if engine is None:
        raise SystemExit("DATABASE_URL is not configured; cannot seed")

    Base.metadata.create_all(engine)
    rows = _load_rows(path)
    logger.info("Loaded %d customer rows from %s", len(rows), path)

    with Session(engine) as db:
        _reconcile(db, rows)

    routes = sorted({code for code, _, _ in rows})
    names_by_route: dict[str, set[str]] = {}
    for code, name, _ in rows:
        names_by_route.setdefault(code, set()).add(name)
    route_counts = {code: len(names) for code, names in names_by_route.items()}
    logger.info(
        "Seeded %d routes: %s", len(routes), ", ".join(f"{code}={route_counts[code]}" for code in routes)
    )

    seen: dict[str, set[str]] = {}
    for code, names in names_by_route.items():
        for name in names:
            seen.setdefault(name, set()).add(code)
    duplicates = {name: sorted(codes) for name, codes in seen.items() if len(codes) > 1}
    if duplicates:
        logger.warning(
            "Names present on more than one route (handled as REVIEW_REQUIRED): %s",
            ", ".join(f"{name} ({', '.join(codes)})" for name, codes in duplicates.items()),
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the customer/route catalog.")
    parser.add_argument(
        "--path", default=str(DEFAULT_PATH), help="Path to the CLIENTES POR RUTA.xlsx workbook"
    )
    args = parser.parse_args()

    path = Path(args.path)
    if not path.is_file():
        print(f"Workbook not found: {path}", file=sys.stderr)
        sys.exit(1)

    seed(path)
    print("Seed completed.")


if __name__ == "__main__":
    main()
