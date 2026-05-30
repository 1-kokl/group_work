"""测试电商模块是否正常工作"""
from app import create_app, db
from app.models.ecommerce_models import Product, Cart, Order, OrderItem


def test_ecommerce_module():
    """测试电商模块"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print(" 开始测试电商模块")
        print("=" * 60)
        
        # 1. 创建所有表
        print("\n1️ 创建数据库表...")
        try:
            db.create_all()
            print(" 数据库表创建成功")
        except Exception as e:
            print(f" 数据库表创建失败: {e}")
            return False
        
        # 2. 检查表是否存在
        print("\n 检查表结构...")
        tables = ['products', 'carts', 'orders', 'order_items']
        for table in tables:
            result = db.session.execute(db.text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")).fetchone()
            if result:
                print(f"  {table} 表存在")
            else:
                print(f"  {table} 表不存在")
                return False
        
        # 3. 测试商品模型
        print("\n 测试商品模型...")
        try:
            product_count = Product.query.count()
            print(f" 商品查询成功，当前商品数: {product_count}")
        except Exception as e:
            print(f" 商品查询失败: {e}")
            return False
        
        # 4. 测试购物车模型
        print("\n测试购物车模型...")
        try:
            cart_count = Cart.query.count()
            print(f" 购物车查询成功，当前购物车项数: {cart_count}")
        except Exception as e:
            print(f" 购物车查询失败: {e}")
            return False
        
        # 5. 测试订单模型
        print("\n 测试订单模型...")
        try:
            order_count = Order.query.count()
            print(f"订单查询成功，当前订单数: {order_count}")
        except Exception as e:
            print(f"订单查询失败: {e}")
            return False
        
        # 6. 测试订单项模型
        print("\n测试订单项模型...")
        try:
            order_item_count = OrderItem.query.count()
            print(f"订单项查询成功，当前订单项数: {order_item_count}")
        except Exception as e:
            print(f"订单项查询失败: {e}")
            return False
        
        print("\n" + "=" * 60)
        print("所有测试通过！电商模块正常工作")
        print("=" * 60)
        return True


if __name__ == "__main__":
    success = test_ecommerce_module()
    exit(0 if success else 1)
