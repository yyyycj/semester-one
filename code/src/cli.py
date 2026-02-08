from __future__ import annotations
from typing import List, Dict, Optional
from .services import AccountingService
from .domain import MovementType


def _input_nonempty(prompt: str) -> str:
    s = input(prompt).strip()
    if not s:
        raise ValueError("Empty input")
    return s


def _input_int(prompt: str) -> int:
    return int(_input_nonempty(prompt))


def _input_lines() -> List[Dict[str, int]]:
    lines: List[Dict[str, int]] = []
    n = _input_int("How many lines? ")
    for i in range(n):
        cid = _input_nonempty(f"  component_id[{i+1}]: ")
        qty = _input_int(f"  qty[{i+1}]: ")
        lines.append({"component_id": cid, "qty": qty})
    return lines


def run_cli(svc: AccountingService) -> None:
    while True:
        print("\n=== Electrical Equipment Production Accounting (CLI) ===")
        print("1) Create product")
        print("2) Create component")
        print("3) Set BOM for product")
        print("4) Create order")
        print("5) Approve order")
        print("6) Register movement (INCOME/ISSUE/RETURN/WRITE_OFF)")
        print("7) Show component stock balance")
        print("8) Register serial unit")
        print("9) Record test PASS/FAIL")
        print("10) Ship unit")
        print("11) Write-off unit")
        print("0) Exit")
        choice = input("Select: ").strip()

        try:
            if choice == "1":
                pid = _input_nonempty("product_id: ")
                name = _input_nonempty("name: ")
                desc = input("description(optional): ").strip()
                svc.create_product(pid, name, desc)
                print("OK")
            elif choice == "2":
                cid = _input_nonempty("component_id: ")
                name = _input_nonempty("name: ")
                unit = input("unit(default pcs): ").strip() or "pcs"
                svc.create_component(cid, name, unit)
                print("OK")
            elif choice == "3":
                pid = _input_nonempty("product_id: ")
                n = _input_int("How many BOM lines? ")
                lines = []
                for i in range(n):
                    cid = _input_nonempty(f"  component_id[{i+1}]: ")
                    qty = _input_int(f"  qty_per_unit[{i+1}]: ")
                    lines.append({"component_id": cid, "qty_per_unit": qty})
                svc.set_bom(pid, lines)
                print("OK")
            elif choice == "4":
                pid = _input_nonempty("product_id: ")
                qty = _input_int("planned_qty: ")
                deadline = input("deadline YYYY-MM-DD(optional): ").strip() or None
                note = input("note(optional): ").strip()
                oid = svc.create_order(pid, qty, deadline, note)
                print(f"OK order_id={oid}")
            elif choice == "5":
                oid = _input_int("order_id: ")
                svc.approve_order(oid)
                print("OK")
            elif choice == "6":
                mtype = _input_nonempty("type (INCOME/ISSUE/RETURN/WRITE_OFF): ").upper()
                lines = _input_lines()
                oid_txt = input("order_id(optional): ").strip()
                oid = int(oid_txt) if oid_txt else None
                note = input("note(optional): ").strip()
                mid = svc.register_movement(mtype, lines, oid, note)
                print(f"OK movement_id={mid}")
            elif choice == "7":
                bal = svc.component_balance()
                if not bal:
                    print("(empty)")
                else:
                    for k in sorted(bal.keys()):
                        print(f"{k}: {bal[k]}")
            elif choice == "8":
                oid = _input_int("order_id: ")
                sn = _input_nonempty("serial_no: ")
                svc.register_unit(oid, sn)
                print("OK")
            elif choice == "9":
                sn = _input_nonempty("serial_no: ")
                res = _input_nonempty("PASS or FAIL: ").upper()
                svc.record_test(sn, passed=(res == "PASS"))
                print("OK")
            elif choice == "10":
                sn = _input_nonempty("serial_no: ")
                svc.ship_unit(sn)
                print("OK")
            elif choice == "11":
                sn = _input_nonempty("serial_no: ")
                svc.write_off_unit(sn)
                print("OK")
            elif choice == "0":
                print("Bye.")
                return
            else:
                print("Unknown option.")
        except Exception as e:
            print(f"ERROR: {e}")