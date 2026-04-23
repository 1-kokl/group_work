"""创建测试数据"""
from app import create_app, db
from app.models.ecommerce_models import Product


def create_test_products():
    """创建测试商品数据"""
    app = create_app()
    
    with app.app_context():
        # 自动创建所有表（如果不存在）
        print("正在检查并创建数据库表...")
        db.create_all()
        print("✅ 数据库表检查完成")
        
        # 检查是否已有数据
        if Product.query.count() > 0:
            print("⚠️ 商品数据已存在，跳过初始化")
            return

        products = [
            Product(
                name="iPhone 15 Pro",
                description="Apple iPhone 15 Pro 256GB 钛金属",
                price=8999.00,
                stock=50,
                category="手机",
                image_url="https://example.com/iphone15.jpg"
            ),
            Product(
                name="MacBook Pro 14",
                description="Apple MacBook Pro 14英寸 M3芯片 16GB+512GB",
                price=12999.00,
                stock=30,
                category="电脑",
                image_url="https://example.com/macbook.jpg"
            ),
            Product(
                name="AirPods Pro 2",
                description="Apple AirPods Pro 第二代 主动降噪",
                price=1899.00,
                stock=100,
                category="耳机",
                image_url="https://example.com/airpods.jpg"
            ),
            Product(
                name="iPad Air",
                description="Apple iPad Air 10.9英寸 M1芯片 64GB",
                price=4799.00,
                stock=40,
                category="平板",
                image_url="https://example.com/ipad.jpg"
            ),
            Product(
                name="Apple Watch Series 9",
                description="Apple Watch Series 9 GPS 45mm",
                price=3199.00,
                stock=60,
                category="手表",
                image_url="https://example.com/watch.jpg"
            )
        ]

        for product in products:
            db.session.add(product)

        db.session.commit()
        print(f"✅ 成功创建 {len(products)} 个测试商品")


if __name__ == "__main__":
    create_test_products()
