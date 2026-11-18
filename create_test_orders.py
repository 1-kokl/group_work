"""
创建测试订单数据脚本
用于生成演示用的商品、购物车和订单数据
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models.ecommerce_models import Product, Cart, Order, OrderItem
from datetime import datetime, timedelta
import uuid
import random


def get_current_user_id():
    """获取当前登录用户的ID
    
    注意：在实际应用中，应该从JWT token中获取当前用户ID
    在测试环境中，我们使用第一个创建订单的用户ID（通常为1）
    """
    # 简单返回1，代表第一个用户
    # 实际项目中应该从 session 或 JWT token 中获取
    print("✅ 使用测试用户 ID: 1")
    print("💡 提示：在实际应用中，订单会自动关联到当前登录用户")
    return 1


def create_test_products():
    """创建测试商品"""
    products = [
        {
            "name": "iPhone 15 Pro",
            "price": 7999.00,
            "description": "Apple iPhone 15 Pro 256GB 原色钛金属",
            "stock": 50,
            "category": "手机数码",
            "image_url": "https://via.placeholder.com/300x300?text=iPhone+15+Pro",
            "status": True
        },
        {
            "name": "MacBook Pro 14",
            "price": 14999.00,
            "description": "Apple MacBook Pro 14英寸 M3 Pro芯片 18GB+512GB",
            "stock": 30,
            "category": "电脑办公",
            "image_url": "https://via.placeholder.com/300x300?text=MacBook+Pro",
            "status": True
        },
        {
            "name": "AirPods Pro 2",
            "price": 1899.00,
            "description": "Apple AirPods Pro 第二代 主动降噪无线耳机",
            "stock": 100,
            "category": "音频设备",
            "image_url": "https://via.placeholder.com/300x300?text=AirPods+Pro",
            "status": True
        },
        {
            "name": "iPad Air 5",
            "price": 4799.00,
            "description": "Apple iPad Air 10.9英寸 M1芯片 64GB WiFi版",
            "stock": 40,
            "category": "平板电脑",
            "image_url": "https://via.placeholder.com/300x300?text=iPad+Air",
            "status": True
        },
        {
            "name": "小米14 Ultra",
            "price": 5999.00,
            "description": "小米14 Ultra 徕卡光学镜头 骁龙8 Gen3 16GB+512GB",
            "stock": 60,
            "category": "手机数码",
            "image_url": "https://via.placeholder.com/300x300?text=Xiaomi+14+Ultra",
            "status": True
        },
        {
            "name": "华为MateBook X Pro",
            "price": 9999.00,
            "description": "华为MateBook X Pro 14.2英寸 i7-1360P 16GB+1TB",
            "stock": 25,
            "category": "电脑办公",
            "image_url": "https://via.placeholder.com/300x300?text=MateBook+X+Pro",
            "status": True
        },
        {
            "name": "Sony WH-1000XM5",
            "price": 2499.00,
            "description": "索尼WH-1000XM5 头戴式无线降噪耳机",
            "stock": 80,
            "category": "音频设备",
            "image_url": "https://via.placeholder.com/300x300?text=Sony+XM5",
            "status": True
        },
        {
            "name": "Nintendo Switch OLED",
            "price": 2399.00,
            "description": "任天堂Switch OLED游戏机 日版续航增强版",
            "stock": 45,
            "category": "游戏娱乐",
            "image_url": "https://via.placeholder.com/300x300?text=Switch+OLED",
            "status": True
        }
    ]

    created_products = []
    for product_data in products:
        # 检查是否已存在
        existing = Product.query.filter_by(name=product_data["name"]).first()
        if not existing:
            product = Product(**product_data)
            db.session.add(product)
            created_products.append(product)
            print(f"✅ 创建商品: {product_data['name']}")
        else:
            created_products.append(existing)
            print(f"⚠️ 商品已存在: {product_data['name']}")

    db.session.commit()
    return created_products


def create_test_orders(user_id=1):
    """为指定用户创建测试订单"""
    
    # 先获取所有商品
    products = Product.query.all()
    if not products:
        print("❌ 没有商品，请先创建商品")
        return []

    orders = []
    
    # 订单1：待支付状态
    order1_items = [
        {"product": products[0], "quantity": 1},  # iPhone 15 Pro
        {"product": products[2], "quantity": 2},  # AirPods Pro x2
    ]
    
    order1 = create_order(
        user_id=user_id,
        items=order1_items,
        status="pending",
        payment_status="unpaid",
        shipping_address="北京市朝阳区建国路100号",
        contact_phone="13800138000",
        remark="请尽快发货"
    )
    orders.append(order1)
    
    # 订单2：已支付状态
    order2_items = [
        {"product": products[1], "quantity": 1},  # MacBook Pro
    ]
    
    order2 = create_order(
        user_id=user_id,
        items=order2_items,
        status="paid",
        payment_status="paid",
        shipping_address="上海市浦东新区世纪大道200号",
        contact_phone="13900139000",
        paid_days_ago=2
    )
    orders.append(order2)
    
    # 订单3：已完成状态
    order3_items = [
        {"product": products[3], "quantity": 1},  # iPad Air
        {"product": products[6], "quantity": 1},  # Sony XM5
    ]
    
    order3 = create_order(
        user_id=user_id,
        items=order3_items,
        status="completed",
        payment_status="paid",
        shipping_address="广州市天河区天河路300号",
        contact_phone="13700137000",
        paid_days_ago=15,
        completed_days_ago=5
    )
    orders.append(order3)
    
    # 订单4：已取消状态
    order4_items = [
        {"product": products[4], "quantity": 1},  # 小米14 Ultra
    ]
    
    order4 = create_order(
        user_id=user_id,
        items=order4_items,
        status="cancelled",
        payment_status="unpaid",
        shipping_address="深圳市南山区科技南路400号",
        contact_phone="13600136000",
        cancelled_days_ago=3
    )
    orders.append(order4)
    
    return orders


def create_order(user_id, items, status="pending", payment_status="unpaid", 
                 shipping_address="", contact_phone="", remark="",
                 paid_days_ago=None, completed_days_ago=None, cancelled_days_ago=None):
    """创建单个订单"""
    
    # 计算总金额
    total_amount = sum(item["product"].price * item["quantity"] for item in items)
    
    # 生成订单号
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_str = str(random.randint(1000, 9999))
    order_no = f"ORD{timestamp}{random_str}"
    
    # 创建订单
    order = Order(
        order_no=order_no,
        user_id=user_id,
        total_amount=total_amount,
        status=status,
        payment_status=payment_status,
        shipping_address=shipping_address,
        contact_phone=contact_phone,
        remark=remark
    )
    
    # 设置时间
    if paid_days_ago:
        order.paid_at = datetime.utcnow() - timedelta(days=paid_days_ago)
        order.created_at = order.paid_at - timedelta(hours=1)
    
    if completed_days_ago and paid_days_ago:
        order.created_at = datetime.utcnow() - timedelta(days=completed_days_ago + 5)
        order.paid_at = datetime.utcnow() - timedelta(days=completed_days_ago + 3)
    
    if cancelled_days_ago:
        order.created_at = datetime.utcnow() - timedelta(days=cancelled_days_ago + 1)
        order.updated_at = datetime.utcnow() - timedelta(days=cancelled_days_ago)
    
    db.session.add(order)
    db.session.flush()
    
    # 创建订单项
    for item in items:
        product = item["product"]
        quantity = item["quantity"]
        subtotal = product.price * quantity
        
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            product_price=product.price,
            quantity=quantity,
            subtotal=subtotal
        )
        db.session.add(order_item)
    
    db.session.commit()
    print(f"✅ 创建订单: {order_no} (状态: {status}, 金额: ¥{total_amount:.2f})")
    return order


def main():
    """主函数"""
    print("=" * 60)
    print("🛒 创建测试订单数据")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        print("\n👤 步骤1: 获取当前登录用户...")
        user_id = get_current_user_id()
        
        print("\n📦 步骤2: 创建测试商品...")
        products = create_test_products()
        print(f"✅ 共创建/找到 {len(products)} 个商品\n")
        
        print("📋 步骤3: 为当前用户创建测试订单...")
        orders = create_test_orders(user_id=user_id)
        print(f"✅ 共创建 {len(orders)} 个订单\n")
        
        print("=" * 60)
        print("✅ 测试数据创建完成！")
        print("=" * 60)
        print(f"\n用户ID: {user_id}")
        print("\n订单列表:")
        for order in orders:
            print(f"  - {order.order_no}: ¥{order.total_amount:.2f} ({order.status})")
        print("\n现在可以登录系统查看订单了！")


if __name__ == "__main__":
    main()
