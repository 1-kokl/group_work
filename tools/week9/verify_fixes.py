"""Bounded before/after proofs on synthetic databases, without an HTTP listener."""
import argparse
import json
from pathlib import Path
import shutil
from common import configure, ROOT

parser = argparse.ArgumentParser()
parser.add_argument("--source", type=Path, default=ROOT)
parser.add_argument("--fixture", type=Path, required=True)
parser.add_argument("--data", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
directory = args.data.resolve()
directory.mkdir(parents=True, exist_ok=False)
for name in ["app.sqlite3", "audit.sqlite3"]:
    shutil.copy2(args.fixture / name, directory / name)
shutil.copytree(args.fixture / "keys", directory / "keys")
configure(directory, args.source.resolve())
import run
from app.extensions import db
from app.models.ecommerce_models import Product, Order, OrderItem, Cart
from sqlalchemy import event
app = run.app
with app.app_context():
    db.create_all()
    if hasattr(run, "apply_database_indexes"):
        run.apply_database_indexes()
client = app.test_client()
token = client.post("/api/v1/auth/login", json={"username": "perf_1", "password": "Week9-Local-Only!"}).json["data"]["access_token"]
headers = {"Authorization": "Bearer "+token}
rows = []
response = client.get("/api/ecommerce/products?per_page=101")
rows.append({"id": "W9-01", "property": "bounded_pagination", "status": response.status_code,
             "returned_items": len(response.json.get("data", {}).get("items", [])), "fixed": response.status_code == 400})
response = client.get("/api/ecommerce/products", headers={"Origin": "https://untrusted.invalid"})
origin = response.headers.get("Access-Control-Allow-Origin")
rows.append({"id": "W9-02", "property": "cors_allowlist", "allow_origin": origin, "fixed": origin is None})
response = client.post("/api/ecommerce/cart", headers=headers, json={"product_id": "perf-product-1", "quantity": -1})
record = {"id": "W9-03", "property": "positive_cart_quantity", "cart_status": response.status_code, "fixed": response.status_code == 400}
if response.status_code == 200:
    response = client.post("/api/ecommerce/orders", headers=headers, json={"shipping_address": "local", "contact_phone": "13800000000"})
    record["order_status"] = response.status_code
    record["order_total"] = response.json.get("data", {}).get("total_amount")
rows.append(record)
# Use a different account and products; two mutations are sufficient for rollback proof.
token = client.post("/api/v1/auth/login", json={"username": "perf_2", "password": "Week9-Local-Only!"}).json["data"]["access_token"]
headers = {"Authorization": "Bearer "+token}
for pid in ["perf-product-2", "perf-product-3"]:
    response = client.post("/api/ecommerce/cart", headers=headers, json={"product_id": pid, "quantity": 1})
    assert response.status_code == 200, response.json
changes = []
with app.app_context():
    engine = db.engine
    before_orders = Order.query.count()
    before_items = OrderItem.query.count()
    before_stock = [db.session.get(Product, f"perf-product-{i}").stock for i in (2, 3)]

def fail_second(conn, cursor, statement, parameters, context, executemany):
    if statement.startswith("UPDATE products SET stock="):
        changes.append(1)
        if len(changes) == 2:
            raise RuntimeError("Controlled local rollback probe")
event.listen(engine, "before_cursor_execute", fail_second)
try:
    response = client.post("/api/ecommerce/orders", headers=headers, json={"shipping_address": "local", "contact_phone": "13800000000"})
finally:
    event.remove(engine, "before_cursor_execute", fail_second)
with app.app_context():
    after_stock = [db.session.get(Product, f"perf-product-{i}").stock for i in (2, 3)]
    order_delta = Order.query.count()-before_orders
    item_delta = OrderItem.query.count()-before_items
rows.append({"id": "W9-04", "property": "atomic_order_rollback", "status": response.status_code,
             "stock_before": before_stock, "stock_after": after_stock, "order_delta": order_delta,
             "item_delta": item_delta, "injected_failures": len(changes),
             "fixed": len(changes) == 2 and response.status_code == 400 and after_stock == before_stock and order_delta == 0 and item_delta == 0})
output = args.output.resolve()
if output.exists():
    raise SystemExit("Refusing to overwrite proof output")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps({"source": str(args.source.resolve()), "synthetic": True, "probes": rows}, indent=2), encoding="utf-8")
print(json.dumps(rows, indent=2))
