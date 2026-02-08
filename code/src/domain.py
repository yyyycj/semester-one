from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List


def utcnow_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


class OrderStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    IN_PRODUCTION = "in_production"
    COMPLETED = "completed"
    CLOSED = "closed"


class MovementType(str, Enum):
    INCOME = "INCOME"
    ISSUE = "ISSUE"
    RETURN = "RETURN"
    WRITE_OFF = "WRITE_OFF"


class UnitState(str, Enum):
    PRODUCED = "produced"
    TEST_FAILED = "test_failed"
    TEST_PASSED = "test_passed"
    SHIPPED = "shipped"
    WRITTEN_OFF = "written_off"


@dataclass(frozen=True)
class Product:
    product_id: str
    name: str
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Component:
    component_id: str
    name: str
    unit: str = "pcs"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BomLine:
    component_id: str
    qty_per_unit: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Order:
    order_id: int
    product_id: str
    planned_qty: int
    status: str
    created_at: str
    deadline: Optional[str] = None
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MovementLine:
    component_id: str
    qty: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Movement:
    movement_id: int
    type: str
    created_at: str
    order_id: Optional[int]
    lines: List[MovementLine]
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["lines"] = [ln.to_dict() for ln in self.lines]
        return d


@dataclass(frozen=True)
class SerialUnit:
    serial_no: str
    order_id: int
    produced_at: str
    state: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)