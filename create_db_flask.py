"""使用 Flask-SQLAlchemy 创建所有表"""
from app import create_app, db
from app.models.ecommerce_models import Product, Cart, Order, OrderItem

app = create_app()

with app.app_context():
    print("创建所有表...")
    db.create_all()
    print("✅ 数据库表创建成功！")

    # 验证表是否创建
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print("\n已创建的表：")
    for table in tables:
        print(f"  ✓ {table}")
