"""
为 testuser (user_id=12) 创建测试订单
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models.ecommerce_models import Product, Order, OrderItem
from datetime import datetime
import random


def create_orders_for_user(user_id=12):
    app = create_app()

    with app.app_context():
        # 获取商品
        products = Product.query.all()
        if not products:
            print("❌ 没有商品，请先创建商品")
            return

        print(f"✅ 找到 {len(products)} 个商品")

        orders_created = []

        # 订单1：待支付（用于测试支付功能）
        product1 = products[0] if len(products) > 0 else products[-1]
        order_no_1 = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}001"
        order1 = Order(
            order_no=order_no_1,
            user_id=user_id,
            total_amount=product1.price,
            status="pending",
            payment_status="unpaid",
            shipping_address="北京市朝阳区测试地址1号",
            contact_phone="13800138000",
            remark="测试订单 - 待支付"
        )
        db.session.add(order1)
        db.session.flush()

        order_item1 = OrderItem(
            order_id=order1.id,
            product_id=product1.id,
            product_name=product1.name,
            product_price=product1.price,
            quantity=1,
            subtotal=product1.price
        )
        db.session.add(order_item1)
        orders_created.append((order_no_1, product1.price, "pending"))

        # 订单2：已支付
        if len(products) > 1:
            product2 = products[1]
            order_no_2 = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}002"
            order2 = Order(
                order_no=order_no_2,
                user_id=user_id,
                total_amount=product2.price * 2,
                status="paid",
                payment_status="paid",
                shipping_address="上海市浦东新区测试地址2号",
                contact_phone="13900139000",
                paid_at=datetime.utcnow(),
                transaction_id=f"TXN_{random.randint(100000, 999999)}"
            )
            db.session.add(order2)
            db.session.flush()

            order_item2 = OrderItem(
                order_id=order2.id,
                product_id=product2.id,
                product_name=product2.name,
                product_price=product2.price,
                quantity=2,
                subtotal=product2.price * 2
            )
            db.session.add(order_item2)
            orders_created.append((order_no_2, product2.price * 2, "paid"))

        # 订单3：已完成
        if len(products) > 2:
            product3 = products[2]
            order_no_3 = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}003"
            order3 = Order(
                order_no=order_no_3,
                user_id=user_id,
                total_amount=product3.price,
                status="completed",
                payment_status="paid",
                shipping_address="广州市天河区测试地址3号",
                contact_phone="13700137000",
                paid_at=datetime.utcnow(),
                transaction_id=f"TXN_{random.randint(100000, 999999)}"
            )
            db.session.add(order3)
            db.session.flush()

            order_item3 = OrderItem(
                order_id=order3.id,
                product_id=product3.id,
                product_name=product3.name,
                product_price=product3.price,
                quantity=1,
                subtotal=product3.price
            )
            db.session.add(order_item3)
            orders_created.append((order_no_3, product3.price, "completed"))

        db.session.commit()

        print(f"\n✅ 为用户 ID={user_id} 创建了 {len(orders_created)} 个订单：")
        for order_no, amount, status in orders_created:
            print(f"   订单号: {order_no}, 金额: ¥{amount:.2f}, 状态: {status}")

        print("\n🎉 现在可以刷新前端页面查看订单了！")


if __name__ == "__main__":
    create_orders_for_user(user_id=12)
