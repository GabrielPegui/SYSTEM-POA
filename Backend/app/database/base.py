"""Declarative base for future SQLAlchemy models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all database models.

    No tables are defined yet; models will be added incrementally following
    the conceptual entities described in ADR-003 (Customer, Route, Product,
    Order, OrderItem, ProcessingHistory).
    """
