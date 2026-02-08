from __future__ import annotations
from typing import Dict, List, Optional
from .domain import (
    Product, Component, BomLine, Order, Movement, MovementLine, SerialUnit,
    utcnow_iso, OrderStatus, MovementType, UnitState
)
from .repositories import Repos


class AccountingService:
    def __init__(self, repos: Repos):
        self.r = repos

    # ---------- Catalog ----------
    def create_product(self, product_id: str, name: str, description: str = "") -> None:
        if self.r.get_product(product_id):
            raise ValueError("Product already exists")
        self.r.add_product(Product(product_id=product_id, name=name, description=description))

    def create_component(self, component_id: str, name: str, unit: str = "pcs") -> None:
        if self.r.get_component(component_id):
            raise ValueError("Component already exists")
        self.r.add_component(Component(component_id=component_id, name=name, unit=unit))

    def set_bom(self, product_id: str, lines: List[Dict[str, int]]) -> None:
        if not self.r.get_product(product_id):
            raise ValueError("Unknown product")
        bom_lines: List[BomLine] = []
        for ln in lines:
            cid = ln["component_id"]
            qty = int(ln["qty_per_unit"])
            if qty <= 0:
                raise ValueError("qty_per_unit must be positive")
            if not self.r.get_component(cid):
                raise ValueError(f"Unknown component: {cid}")
            bom_lines.append(BomLine(component_id=cid, qty_per_unit=qty))
        if not bom_lines:
            raise ValueError("BOM cannot be empty")
        self.r.set_bom(product_id, bom_lines)

    # ---------- Orders ----------
    def create_order(self, product_id: str, planned_qty: int, deadline: Optional[str] = None, note: str = "") -> int:
        if not self.r.get_product(product_id):
            raise ValueError("Unknown product")
        if planned_qty <= 0:
            raise ValueError("planned_qty must be positive")
        order_id = self.r.new_order_id()
        o = Order(
            order_id=order_id,
            product_id=product_id,
            planned_qty=int(planned_qty),
            status=OrderStatus.DRAFT.value,
            created_at=utcnow_iso(),
            deadline=deadline,
            note=note,
        )
        self.r.add_order(o)
        return order_id

    def approve_order(self, order_id: int) -> None:
        o = self._must_order(order_id)
        if o["status"] != OrderStatus.DRAFT.value:
            raise ValueError("Only draft orders can be approved")
        if not self.r.get_bom(o["product_id"]):
            raise ValueError("BOM is required before approval")
        self.r.update_order_status(order_id, OrderStatus.APPROVED.value)

    def mark_in_production_if_needed(self, order_id: int) -> None:
        o = self._must_order(order_id)
        if o["status"] == OrderStatus.APPROVED.value:
            self.r.update_order_status(order_id, OrderStatus.IN_PRODUCTION.value)

    # ---------- Inventory ----------
    def component_balance(self) -> Dict[str, int]:
        bal: Dict[str, int] = {}
        for mv in self.r.list_movements():
            mtype = mv["type"]
            sign = 1 if mtype in (MovementType.INCOME.value, MovementType.RETURN.value) else -1
            for ln in mv["lines"]:
                cid = ln["component_id"]
                qty = int(ln["qty"])
                bal[cid] = bal.get(cid, 0) + sign * qty
        return bal

    def register_movement(self, mtype: str, lines: List[Dict[str, int]], order_id: Optional[int] = None, note: str = "") -> int:
        if mtype not in {x.value for x in MovementType}:
            raise ValueError("Unknown movement type")

        if order_id is not None:
            o = self._must_order(order_id)
            if mtype == MovementType.ISSUE.value:
                if o["status"] not in (OrderStatus.APPROVED.value, OrderStatus.IN_PRODUCTION.value):
                    raise ValueError("ISSUE is allowed only for approved/in_production orders")

        mv_lines: List[MovementLine] = []
        for ln in lines:
            cid = ln["component_id"]
            qty = int(ln["qty"])
            if qty <= 0:
                raise ValueError("qty must be positive")
            if not self.r.get_component(cid):
                raise ValueError(f"Unknown component: {cid}")
            mv_lines.append(MovementLine(component_id=cid, qty=qty))

        # negative stock prevention
        if mtype in (MovementType.ISSUE.value, MovementType.WRITE_OFF.value):
            bal = self.component_balance()
            for ln in mv_lines:
                if bal.get(ln.component_id, 0) - ln.qty < 0:
                    raise ValueError(f"Negative stock is not allowed for component {ln.component_id}")

        mid = self.r.new_movement_id()
        m = Movement(
            movement_id=mid,
            type=mtype,
            created_at=utcnow_iso(),
            order_id=order_id,
            lines=mv_lines,
            note=note,
        )
        self.r.add_movement(m)

        if mtype == MovementType.ISSUE.value and order_id is not None:
            self.mark_in_production_if_needed(order_id)

        return mid

    # ---------- Units ----------
    def register_unit(self, order_id: int, serial_no: str) -> None:
        o = self._must_order(order_id)
        if o["status"] not in (OrderStatus.IN_PRODUCTION.value, OrderStatus.APPROVED.value):
            raise ValueError("Order must be approved or in production")
        if self.r.get_unit(serial_no):
            raise ValueError("Serial number already exists")
        self.mark_in_production_if_needed(order_id)
        u = SerialUnit(serial_no=serial_no, order_id=order_id, produced_at=utcnow_iso(), state=UnitState.PRODUCED.value)
        self.r.add_unit(u)

    def record_test(self, serial_no: str, passed: bool) -> None:
        u = self._must_unit(serial_no)
        if u["state"] in (UnitState.SHIPPED.value, UnitState.WRITTEN_OFF.value):
            raise ValueError("Cannot test shipped/written-off unit")
        self.r.update_unit_state(serial_no, UnitState.TEST_PASSED.value if passed else UnitState.TEST_FAILED.value)

    def ship_unit(self, serial_no: str) -> None:
        u = self._must_unit(serial_no)
        if u["state"] != UnitState.TEST_PASSED.value:
            raise ValueError("Unit must have PASS test before shipment")
        self.r.update_unit_state(serial_no, UnitState.SHIPPED.value)

    def write_off_unit(self, serial_no: str) -> None:
        u = self._must_unit(serial_no)
        if u["state"] == UnitState.SHIPPED.value:
            raise ValueError("Cannot write-off shipped unit")
        self.r.update_unit_state(serial_no, UnitState.WRITTEN_OFF.value)

    # ---------- Helpers ----------
    def _must_order(self, order_id: int) -> Dict:
        o = self.r.get_order(order_id)
        if o is None:
            raise ValueError("Order not found")
        return o

    def _must_unit(self, serial_no: str) -> Dict:
        u = self.r.get_unit(serial_no)
        if u is None:
            raise ValueError("Serial unit not found")
        return u