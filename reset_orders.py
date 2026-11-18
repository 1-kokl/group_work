"""重置所有订单到初始状态"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models.ecommerce_models import Order

app = create_app()

with app.app_context():
    # 查询所有订单
    orders = Order.query.all()
    
    print(f"找到 {len(orders)} 个订单")
    print("\n开始重置订单状态...")
    
    for order in orders:
        # 重置为待支付状态
        order.status = "pending"
        order.payment_status = "unpaid"
        order.payment_method = None
        order.transaction_id = None
        order.paid_at = None
        
    db.session.commit()
    
    print("✅ 所有订单已重置为待支付状态！")
    print("\n订单列表:")
    for order in orders:
        print(f"  - {order.order_no}: status={order.status}, payment_status={order.payment_status}")
