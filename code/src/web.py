from __future__ import annotations

from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash

from .storage import JsonStore
from .repositories import Repos
from .services import AccountingService


BASE_DIR = Path(__file__).resolve().parent.parent

app = Flask(
    __name__,
    template_folder=str(Path(__file__).resolve().parent / "templates"),
    static_folder=str(BASE_DIR / "static"),
    static_url_path="/static",
)
app.secret_key = "dev-secret"

# init backend (same as CLI)
store = JsonStore(BASE_DIR / "data")
repos = Repos(store)
svc = AccountingService(repos)


@app.get("/")
def index():
    return render_template("index.html")


# ---------- Products ----------
@app.get("/products/new")
def product_new():
    return render_template("product_new.html")


@app.post("/products/new")
def product_new_post():
    try:
        product_id = request.form["product_id"].strip()
        name = request.form["name"].strip()
        description = request.form.get("description", "").strip()
        svc.create_product(product_id, name, description)
        flash("Product created", "ok")
        return redirect(url_for("index"))
    except Exception as e:
        flash(f"ERROR: {e}", "err")
        return redirect(url_for("product_new"))


# ---------- Components ----------
@app.get("/components/new")
def component_new():
    return render_template("component_new.html")


@app.post("/components/new")
def component_new_post():
    try:
        component_id = request.form["component_id"].strip()
        name = request.form["name"].strip()
        unit = request.form.get("unit", "pcs").strip() or "pcs"
        svc.create_component(component_id, name, unit)
        flash("Component created", "ok")
        return redirect(url_for("index"))
    except Exception as e:
        flash(f"ERROR: {e}", "err")
        return redirect(url_for("component_new"))


# ---------- BOM ----------
@app.get("/bom/set")
def bom_set():
    return render_template("bom_set.html")


@app.post("/bom/set")
def bom_set_post():
    """
    input example:
      product_id: P-100
      lines:
        C-01=2
        C-02=1
    """
    try:
        product_id = request.form["product_id"].strip()
        raw = request.form["lines"].strip().splitlines()
        lines = []
        for ln in raw:
            ln = ln.strip()
            if not ln:
                continue
            if "=" not in ln:
                raise ValueError("BOM line format must be: component_id=qty_per_unit")
            cid, qty = ln.split("=", 1)
            lines.append({"component_id": cid.strip(), "qty_per_unit": int(qty.strip())})

        svc.set_bom(product_id, lines)
        flash("BOM saved", "ok")
        return redirect(url_for("index"))
    except Exception as e:
        flash(f"ERROR: {e}", "err")
        return redirect(url_for("bom_set"))


# ---------- Orders ----------
@app.get("/orders/new")
def order_new():
    return render_template("order_new.html")


@app.post("/orders/new")
def order_new_post():
    try:
        product_id = request.form["product_id"].strip()
        planned_qty = int(request.form["planned_qty"].strip())
        deadline = request.form.get("deadline", "").strip() or None
        note = request.form.get("note", "").strip()
        oid = svc.create_order(product_id, planned_qty, deadline, note)
        flash(f"Order created: order_id={oid}", "ok")
        return redirect(url_for("index"))
    except Exception as e:
        flash(f"ERROR: {e}", "err")
        return redirect(url_for("order_new"))


@app.get("/orders/approve")
def order_approve():
    return render_template("order_approve.html")


@app.post("/orders/approve")
def order_approve_post():
    try:
        order_id = int(request.form["order_id"].strip())
        svc.approve_order(order_id)
        flash("Order approved", "ok")
        return redirect(url_for("index"))
    except Exception as e:
        flash(f"ERROR: {e}", "err")
        return redirect(url_for("order_approve"))


# ---------- Movements ----------
@app.get("/movements/new")
def movement_new():
    return render_template("movement_new.html")


@app.post("/movements/new")
def movement_new_post():
    """
    lines example:
      C-01=10
      C-02=5
    """
    try:
        mtype = request.form["type"].strip().upper()
        order_id_txt = request.form.get("order_id", "").strip()
        order_id = int(order_id_txt) if order_id_txt else None
        note = request.form.get("note", "").strip()

        raw = request.form["lines"].strip().splitlines()
        lines = []
        for ln in raw:
            ln = ln.strip()
            if not ln:
                continue
            if "=" not in ln:
                raise ValueError("Movement line format must be: component_id=qty")
            cid, qty = ln.split("=", 1)
            lines.append({"component_id": cid.strip(), "qty": int(qty.strip())})

        mid = svc.register_movement(mtype, lines, order_id, note)
        flash(f"Movement saved: movement_id={mid}", "ok")
        return redirect(url_for("index"))
    except Exception as e:
        flash(f"ERROR: {e}", "err")
        return redirect(url_for("movement_new"))


# ---------- Units ----------
@app.get("/units/register")
def unit_register():
    return render_template("unit_register.html")


@app.post("/units/register")
def unit_register_post():
    try:
        order_id = int(request.form["order_id"].strip())
        serial_no = request.form["serial_no"].strip()
        svc.register_unit(order_id, serial_no)
        flash("Serial unit registered", "ok")
        return redirect(url_for("index"))
    except Exception as e:
        flash(f"ERROR: {e}", "err")
        return redirect(url_for("unit_register"))


@app.get("/units/test")
def unit_test():
    return render_template("unit_test.html")


@app.post("/units/test")
def unit_test_post():
    try:
        serial_no = request.form["serial_no"].strip()
        result = request.form["result"].strip().upper()
        svc.record_test(serial_no, passed=(result == "PASS"))
        flash("Test recorded", "ok")
        return redirect(url_for("index"))
    except Exception as e:
        flash(f"ERROR: {e}", "err")
        return redirect(url_for("unit_test"))


@app.get("/units/ship")
def unit_ship():
    return render_template("unit_ship.html")


@app.post("/units/ship")
def unit_ship_post():
    try:
        serial_no = request.form["serial_no"].strip()
        svc.ship_unit(serial_no)
        flash("Unit shipped", "ok")
        return redirect(url_for("index"))
    except Exception as e:
        flash(f"ERROR: {e}", "err")
        return redirect(url_for("unit_ship"))


# ---------- Reports ----------
@app.get("/reports/stock")
def report_stock():
    bal = svc.component_balance()
    rows = sorted(bal.items(), key=lambda x: x[0])
    return render_template("report_stock.html", rows=rows)


def main():
    app.run(host="127.0.0.1", port=5000, debug=True)


if __name__ == "__main__":
    main()