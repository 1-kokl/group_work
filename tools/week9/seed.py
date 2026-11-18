"""Deterministic synthetic fixtures; refuses to overwrite any existing database."""
import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path
import sqlite3
from common import configure, ROOT

parser = argparse.ArgumentParser()
parser.add_argument("--data", required=True)
parser.add_argument("--source", default=str(ROOT))
parser.add_argument("--products", type=int, default=20000)
parser.add_argument("--users", type=int, default=100)
args = parser.parse_args()
directory = Path(args.data).resolve()
if (directory / "app.sqlite3").exists():
    raise SystemExit("Refusing to overwrite existing data; select a new --data directory")
configure(directory, args.source)
from run import app
from app.extensions import db
from app.services.SM3_Service import hash_password
with app.app_context():
    db.create_all()
conn = sqlite3.connect(directory / "app.sqlite3")
password = "Week9-Local-Only!"
hashed = hash_password(password)
conn.executemany("INSERT INTO users (id,username,password_hash,phone,phone_encrypted,role) VALUES (?,?,?,?,?,?)", [
    (i, f"perf_{i}", hashed, "13800000000", "synthetic", "user") for i in range(1, args.users + 1)
] + [(1000+i, f"seller_{i}", hashed, "13800000000", "synthetic", "merchant") for i in range(20)])
start = datetime(2026, 1, 1)
conn.executemany("INSERT INTO products (id,name,description,price,stock,category,status,created_at,updated_at,created_by) VALUES (?,?,?,?,?,?,?,?,?,?)", [
    (f"perf-product-{i}", f"Local product {i}", "Synthetic acceptance data", float(10+i%90),
     1000000, f"category-{i%10:02d}", 1, str(start+timedelta(seconds=i)), str(start), 1000+i%20)
    for i in range(1, args.products+1)
])
# Match the existing init_ecommerce_db.py indexes in the baseline as well.
for ddl in ["CREATE INDEX IF NOT EXISTS idx_carts_user_id ON carts(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)",
            "CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id)"]:
    conn.execute(ddl)
conn.commit()
conn.close()
(directory / "fixture.json").write_text(json.dumps({
    "products": args.products, "users": args.users, "merchants": 20,
    "username_pattern": "perf_<1..users>", "password": password,
    "stock_per_product": 1000000, "synthetic": True,
}, indent=2), encoding="utf-8")
print("Fixture ready:", directory)
