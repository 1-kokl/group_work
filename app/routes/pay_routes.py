# app/routes/pay_routes.py
from flask import Blueprint, jsonify, request
import time
import base64
import hashlib
import json

# 创建蓝图
pay_bp = Blueprint('pay', __name__, url_prefix='/api/pay')

# 从 ecommerce_routes 导入共享的订单数据
from app.routes.ecommerce_routes import orders_db

def generate_simple_signature(sign_str):
    """
    简化版签名：使用 SHA256 + Base64
    注意：生产环境应使用 SM2/SM3，但为了测试连通性，我们先这样写
    """
    hash_val = hashlib.sha256(sign_str.encode('utf-8')).hexdigest()
    return base64.b64encode(hash_val.encode('utf-8')).decode('utf-8')

@pay_bp.route('/create/<order_id>', methods=['POST'])
def create_payment(order_id):
    # 获取订单
    order = orders_db.get(order_id)
    
    if not order:
        return jsonify({"code": 404, "msg": "订单不存在"}), 404
    
    if order.get('payment_status') == 'paid':
        return jsonify({"code": 400, "msg": "订单已支付"}), 400
    
    # 1. 准备参数
    timestamp = int(time.time())  # 【关键】必须是整数时间戳
    merchant_id = "MERCHANT_001"
    amount = order['total_amount']
    
    # 2. 构造待签名字符串 (与银行端保持一致)
    sign_str = f"{order_id}|{amount}|{merchant_id}|{timestamp}"
    
    # 3. 生成签名
    signature = generate_simple_signature(sign_str)
    
    # 4. 生成支付 URL (指向银行的 /pay 接口)
    payment_url = (
        f"http://localhost:8080/pay"
        f"?order_id={order_id}"
        f"&amount={amount}"
        f"&merchant_id={merchant_id}"
        f"&timestamp={timestamp}"
        f"&signature={signature}"
        f"&callback_url=http://localhost:5000/api/pay/result"
    )
    
    # 5. 返回结果
    return jsonify({
        "code": 200,
        "data": {
            "payment_url": payment_url,
            "timestamp": timestamp,
            "signature": signature,
            "order_id": order_id,
            "amount": amount
        }
    }), 200
@pay_bp.route('/callback', methods=['POST'])
def handle_callback():
    """
    接收银行的支付结果通知
    """
    try:
        data = request.json
        print(f"📥 收到银行回调: {data}")
        
        # 简化版：只要收到回调，就认为支付成功
        # 实际项目中需要验签和解密
        order_id = data.get('order_id')
        transaction_id = data.get('transaction_id', 'TXN_MOCK_123')
        
        if order_id and order_id in orders_db:
            # 【关键】更新内存中的订单状态
            orders_db[order_id]['payment_status'] = 'paid'
            orders_db[order_id]['transaction_id'] = transaction_id
            orders_db[order_id]['status'] = 'paid' # 同时更新订单总状态
            
            print(f"✅ 订单 {order_id} 状态已更新为 paid")
            return jsonify({"code": 200, "msg": "OK"}), 200
        else:
            print(f"❌ 未找到订单 {order_id}")
            return jsonify({"code": 404, "msg": "Order not found"}), 404
            
    except Exception as e:
        print(f"❌ 处理回调异常: {e}")
        return jsonify({"code": 500, "msg": str(e)}), 500