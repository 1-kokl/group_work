"""Behavioral regressions for concurrency, authorization and optimization safety."""
from concurrent.futures import ThreadPoolExecutor
import time
import pytest


def test_sm3_native_matches_reference(app):
    from app.services.SM3_Service import sm3_hash
    from gmssl.sm3 import sm3_hash as reference, bytes_to_list
    for data in [b"", b"abc", "中文密码".encode(), bytes(range(256))*3]:
        assert sm3_hash(data) == reference(bytes_to_list(data))


def test_cached_jwt_still_checks_expiry_logout_and_tampering(app, monkeypatch):
    from app.services.JWT_SM2_Utils import JWTSM2Service
    service = JWTSM2Service()
    token = service.generate_token({"username": "local", "nested": {"value": 1}}, expires_in=5)
    payload = service.verify_token(token)
    payload["nested"]["value"] = 9
    assert service.verify_token(token)["nested"]["value"] == 1
    parts = token.split(".")
    parts[1] = service._base64_encode({"username": "admin", "exp": int(time.time())+100})
    with pytest.raises(RuntimeError):
        service.verify_token(".".join(parts))
    original = time.time
    monkeypatch.setattr(time, "time", lambda: original()+10)
    with pytest.raises(RuntimeError):
        service.verify_token(token)
    monkeypatch.setattr(time, "time", original)
    token = service.generate_token({"username": "local"})
    service.verify_token(token)
    service.add_to_blacklist(token)
    with pytest.raises(RuntimeError):
        service.verify_token(token)


def test_jwt_cache_is_bounded_and_tokens_are_unique(app):
    from app.services.JWT_SM2_Utils import JWTSM2Service
    service = JWTSM2Service()
    service._cache_capacity = 2
    tokens = [service.generate_token({"username": "same"}) for _ in range(3)]
    assert len(set(tokens)) == 3
    for token in tokens:
        service.verify_token(token)
    assert len(service._verified) == 2


def test_products_preserve_seller_and_validate_paging(app, buyer, product):
    user_id, _ = buyer
    product(seller=user_id)
    from app.services.user_service import user_service
    expected = user_service.get_user_by_id(user_id).username
    client = app.test_client()
    response = client.get("/api/ecommerce/products?category=regression&per_page=100")
    assert response.status_code == 200
    assert any(row["seller_username"] == expected for row in response.json["data"]["items"])
    assert client.get("/api/ecommerce/products?per_page=1000000").status_code == 400
    assert client.get("/api/ecommerce/products?page=0").status_code == 400
    assert client.get("/api/ecommerce/products?status=false").json["data"]["items"] == []


@pytest.mark.parametrize("quantity", [0, -1, 1.5, True])
def test_cart_rejects_invalid_quantity(app, buyer, product, quantity):
    _, headers = buyer
    response = app.test_client().post("/api/ecommerce/cart", headers=headers,
                                      json={"product_id": product(), "quantity": quantity})
    assert response.status_code == 400
    client = app.test_client()
    created = client.post("/api/ecommerce/cart", headers=headers,
                          json={"product_id": product(), "quantity": 1})
    assert created.status_code == 200
    assert client.put("/api/ecommerce/cart/"+created.json["data"]["id"], headers=headers,
                      json={"quantity": quantity}).status_code == 400


def test_order_failure_rolls_back_all_products_and_items(app, buyer, product, monkeypatch):
    _, headers = buyer
    first, second = product(stock=10), product(stock=10)
    client = app.test_client()
    for pid in (first, second):
        assert client.post("/api/ecommerce/cart", headers=headers, json={"product_id": pid, "quantity": 1}).status_code == 200
    from app.models.ecommerce_models import Product, Order, Cart
    from app.extensions import db
    from sqlalchemy import event
    changes = []
    with app.app_context():
        engine = db.engine
        before_orders = Order.query.count()

    def fail_second_update(conn, cursor, statement, parameters, context, executemany):
        if statement.startswith("UPDATE products SET stock="):
            changes.append(1)
            if len(changes) == 2:
                raise RuntimeError("Injected failure after the first stock change")
    event.listen(engine, "before_cursor_execute", fail_second_update)
    try:
        result = client.post("/api/ecommerce/orders", headers=headers,
                             json={"shipping_address": "local", "contact_phone": "13800000000"})
        assert result.status_code == 400
    finally:
        event.remove(engine, "before_cursor_execute", fail_second_update)
    with app.app_context():
        assert db.session.get(Product, first).stock == 10
        assert db.session.get(Product, second).stock == 10
        assert Order.query.count() == before_orders
        assert Cart.query.filter(Cart.product_id.in_([first, second])).count() == 2


def test_duplicate_checkout_and_cancel_are_atomic(app, buyer, product):
    user_id, headers = buyer
    pid = product(stock=10)
    assert app.test_client().post("/api/ecommerce/cart", headers=headers, json={"product_id": pid, "quantity": 2}).status_code == 200
    def checkout(_):
        return app.test_client().post("/api/ecommerce/orders", headers=headers,
                                     json={"shipping_address": "local", "contact_phone": "13800000000"})
    with ThreadPoolExecutor(max_workers=8) as pool:
        responses = list(pool.map(checkout, range(8)))
    assert sum(r.status_code == 201 for r in responses) == 1
    order = next(r.json["data"] for r in responses if r.status_code == 201)
    from app.extensions import db
    from app.models.ecommerce_models import Product, Order, OrderItem
    with app.app_context():
        assert db.session.get(Product, pid).stock == 8
        assert Order.query.filter_by(user_id=user_id).count() == 1
        assert OrderItem.query.filter_by(order_id=order["id"]).count() == 1
    def cancel(_):
        return app.test_client().post(f"/api/ecommerce/orders/{order['id']}/cancel", headers=headers)
    with ThreadPoolExecutor(max_workers=8) as pool:
        responses = list(pool.map(cancel, range(8)))
    assert sum(r.status_code == 200 for r in responses) == 1
    with app.app_context():
        assert db.session.get(Product, pid).stock == 10


def test_hot_product_cannot_oversell(app, product):
    from app.services.user_service import user_service
    from uuid import uuid4
    pid = product(stock=5)
    headers = []
    for i in range(16):
        username = "hot_"+uuid4().hex
        assert user_service.register(username, "Local-123!", "13800000000", "synthetic")["success"]
        client = app.test_client()
        token = client.post("/api/v1/auth/login", json={"username": username, "password": "Local-123!"}).json["data"]["access_token"]
        header = {"Authorization": "Bearer "+token}
        headers.append(header)
        assert client.post("/api/ecommerce/cart", headers=header, json={"product_id": pid, "quantity": 1}).status_code == 200
    def checkout(header):
        return app.test_client().post("/api/ecommerce/orders", headers=header,
                                     json={"shipping_address": "local", "contact_phone": "13800000000"})
    with ThreadPoolExecutor(max_workers=16) as pool:
        responses = list(pool.map(checkout, headers))
    assert sum(r.status_code == 201 for r in responses) == 5
    assert all(r.status_code in (201, 400) for r in responses)
    from app.extensions import db
    from app.models.ecommerce_models import Product, OrderItem
    with app.app_context():
        assert db.session.get(Product, pid).stock == 0
        assert OrderItem.query.filter_by(product_id=pid).count() == 5


def test_orders_remain_owned_and_mfa_token_is_rejected(app, buyer, product):
    user_id, headers = buyer
    client = app.test_client()
    assert client.post("/api/ecommerce/cart", headers=headers, json={"product_id": product(), "quantity": 1}).status_code == 200
    order = client.post("/api/ecommerce/orders", headers=headers,
                        json={"shipping_address": "local", "contact_phone": "13800000000"}).json["data"]
    from app.services.JWT_SM2_Utils import jwt_service
    other = {"Authorization": "Bearer "+jwt_service.generate_token({"username": "other", "user_id": user_id+99999, "role": "user"})}
    assert client.get(f"/api/ecommerce/orders/{order['id']}", headers=other).status_code == 404
    assert client.post(f"/api/ecommerce/orders/{order['id']}/cancel", headers=other).status_code == 400
    pending = {"Authorization": "Bearer "+jwt_service.generate_token({"username": "admin", "role": "admin", "mfa": "pending"})}
    assert client.post("/api/ecommerce/orders", headers=pending, json={}).status_code == 401


def test_cors_allowlist_and_cookie_only_requests(app, buyer, product):
    client = app.test_client()
    url = "/api/ecommerce/products"
    assert client.get(url, headers={"Origin": "https://untrusted.invalid"}).headers.get("Access-Control-Allow-Origin") is None
    assert client.get(url, headers={"Origin": "http://localhost:8080"}).headers.get("Access-Control-Allow-Origin") == "http://localhost:8080"
    # Authorization uses an explicit Bearer header; cookies alone confer no access.
    client.set_cookie("access_token", buyer[1]["Authorization"].split()[1])
    assert client.post("/api/ecommerce/cart", json={"product_id": product(), "quantity": 1}).status_code == 401
