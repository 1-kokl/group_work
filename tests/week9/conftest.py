import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/week9"))


@pytest.fixture(scope="session")
def app(tmp_path_factory):
    from common import configure
    configure(tmp_path_factory.mktemp("week9-regression"), ROOT)
    import run
    from app.extensions import db
    with run.app.app_context():
        db.create_all()
        run.apply_database_indexes()
    run.app.config.update(TESTING=True)
    return run.app


@pytest.fixture
def buyer(app):
    from uuid import uuid4
    from app.services.user_service import user_service
    username = "test_"+uuid4().hex
    result = user_service.register(username, "Test-local-123!", "13800000000", "synthetic")
    assert result["success"]
    user = user_service.get_user_by_username(username)
    client = app.test_client()
    response = client.post("/api/v1/auth/login", json={"username": username, "password": "Test-local-123!"})
    assert response.status_code == 200
    return user.id, {"Authorization": "Bearer "+response.json["data"]["access_token"]}


@pytest.fixture
def product(app):
    def make(stock=10, name="Regression product", seller=None):
        from app.services.ecommerce_service import ProductService
        with app.app_context():
            result = ProductService.create_product(name, 12.5, stock=stock, category="regression", created_by=seller)
            assert result["success"], result
            return result["data"]["id"]
    return make
