from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from .storage import JsonStore
from .domain import Product, Component, BomLine, Order, Movement, MovementLine, SerialUnit, utcnow_iso, OrderStatus


@dataclass
class Meta:
    next_order_id: int = 1
    next_movement_id: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {"next_order_id": self.next_order_id, "next_movement_id": self.next_movement_id}

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Meta":
        return Meta(next_order_id=int(d.get("next_order_id", 1)), next_movement_id=int(d.get("next_movement_id", 1)))


class Repos:
    """
    Text-file repositories (JSON). Later you can replace with MySQL implementations.
    """
    def __init__(self, store: JsonStore):
        self.store = store
        self.meta = Meta.from_dict(self.store.load("meta", {}))
        self.products: Dict[str, Dict[str, Any]] = self.store.load("products", {})
        self.components: Dict[str, Dict[str, Any]] = self.store.load("components", {})
        self.bom: Dict[str, List[Dict[str, Any]]] = self.store.load("bom", {})  # product_id -> lines
        self.orders: Dict[str, Dict[str, Any]] = self.store.load("orders", {})  # order_id str -> dict
        self.movements: Dict[str, Dict[str, Any]] = self.store.load("movements", {})  # movement_id str -> dict
        self.units: Dict[str, Dict[str, Any]] = self.store.load("units", {})  # serial_no -> dict

    def flush_all(self) -> None:
        self.store.save("meta", self.meta.to_dict())
        self.store.save("products", self.products)
        self.store.save("components", self.components)
        self.store.save("bom", self.bom)
        self.store.save("orders", self.orders)
        self.store.save("movements", self.movements)
        self.store.save("units", self.units)

    # --- Products ---
    def add_product(self, p: Product) -> None:
        self.products[p.product_id] = p.to_dict()
        self.store.save("products", self.products)

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        return self.products.get(product_id)

    # --- Components ---
    def add_component(self, c: Component) -> None:
        self.components[c.component_id] = c.to_dict()
        self.store.save("components", self.components)

    def get_component(self, component_id: str) -> Optional[Dict[str, Any]]:
        return self.components.get(component_id)

    # --- BOM ---
    def set_bom(self, product_id: str, lines: List[BomLine]) -> None:
        self.bom[product_id] = [ln.to_dict() for ln in lines]
        self.store.save("bom", self.bom)

    def get_bom(self, product_id: str) -> List[Dict[str, Any]]:
        return list(self.bom.get(product_id, []))

    # --- Orders ---
    def new_order_id(self) -> int:
        oid = self.meta.next_order_id
        self.meta.next_order_id += 1
        self.store.save("meta", self.meta.to_dict())
        return oid

    def add_order(self, o: Order) -> None:
        self.orders[str(o.order_id)] = o.to_dict()
        self.store.save("orders", self.orders)

    def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        return self.orders.get(str(order_id))

    def update_order_status(self, order_id: int, status: str) -> None:
        o = self.get_order(order_id)
        if o is None:
            raise ValueError("Order not found")
        o["status"] = status
        self.orders[str(order_id)] = o
        self.store.save("orders", self.orders)

    # --- Movements ---
    def new_movement_id(self) -> int:
        mid = self.meta.next_movement_id
        self.meta.next_movement_id += 1
        self.store.save("meta", self.meta.to_dict())
        return mid

    def add_movement(self, m: Movement) -> None:
        self.movements[str(m.movement_id)] = m.to_dict()
        self.store.save("movements", self.movements)

    def list_movements(self) -> List[Dict[str, Any]]:
        # sort by id
        return [self.movements[k] for k in sorted(self.movements.keys(), key=lambda x: int(x))]

    # --- Units ---
    def add_unit(self, u: SerialUnit) -> None:
        self.units[u.serial_no] = u.to_dict()
        self.store.save("units", self.units)

    def get_unit(self, serial_no: str) -> Optional[Dict[str, Any]]:
        return self.units.get(serial_no)

    def update_unit_state(self, serial_no: str, state: str) -> None:
        u = self.get_unit(serial_no)
        if u is None:
            raise ValueError("Serial unit not found")
        u["state"] = state
        self.units[serial_no] = u
        self.store.save("units", self.units)