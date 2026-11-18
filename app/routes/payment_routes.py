"""
支付路由 - 处理支付相关的HTTP请求
"""
from flask import Blueprint, request, jsonify, redirect, render_template_string
from app.services.payment_service import PaymentService
from app.middleware.jwt_auth import jwt_required
from app.utils.response import api_response
from app.models.ecommerce_models import Order
from app.extensions import db
import time
from datetime import datetime

pay_bp = Blueprint("payment", __name__, url_prefix="/api/pay")


@pay_bp.route("/create/<order_id>", methods=["POST"])
@jwt_required
def create_payment(order_id):
    """
    创建支付请求
    1. 验证订单
    2. 生成签名
    3. 返回支付跳转URL
    """
    try:
        from app.services.SM3_Service import sm3_hash
        
        user_id = request.user_info.get("user_id")
        
        # 查询订单
        order = Order.query.filter_by(id=order_id, user_id=user_id).first()
        if not order:
            return api_response(404, "订单不存在")
        
        # 检查订单状态
        if order.payment_status == "paid":
            return api_response(400, "订单已支付")
        
        if order.status != "pending":
            return api_response(400, "订单状态不正确")
        
        # 更新支付状态为"支付中"
        order.payment_status = "paying"
        db.session.commit()
        
        # 生成签名
        timestamp = int(time.time())
        sign_str = f"{order.order_no}|{order.total_amount}|ECOMMERCE_001|{timestamp}"
        signature = sm3_hash(sign_str)
        
        # 生成支付URL - 包含所有必要参数
        callback_url = "http://localhost:5000/api/pay/result"
        bank_url = (
            f"http://localhost:8080/pay?"
            f"order_id={order.order_no}"
            f"&amount={order.total_amount}"
            f"&merchant_id=ECOMMERCE_001"
            f"&timestamp={timestamp}"
            f"&signature={signature}"
            f"&callback_url={callback_url}"
        )
        
        payment_info = {
            "payment_url": bank_url,
            "order_no": order.order_no,
            "amount": order.total_amount
        }
        
        return api_response(200, "支付请求创建成功", payment_info)
    
    except Exception as e:
        db.session.rollback()
        return api_response(500, f"创建支付失败: {str(e)}")


@pay_bp.route("/result", methods=["GET"])
def payment_result():
    """
    银行同步跳转结果页
    支持两种模式：
    1. 简单模式：接收 status 和 order_id 参数
    2. 加密模式：接收 encrypted_key, iv, ciphertext 参数
    """
    try:
        # 检查是否是简单模式（银行直接跳转）
        status = request.args.get("status")
        order_id = request.args.get("order_id")
        
        if status and order_id:
            # 简单模式：根据订单号查询订单信息
            order = Order.query.filter_by(order_no=order_id).first()
            
            if status == "success":
                return render_template_string(PAYMENT_RESULT_HTML,
                                            success=True,
                                            message="支付成功",
                                            data={
                                                "order_id": order_id,
                                                "transaction_id": order.transaction_id if order else "未知",
                                                "amount": order.total_amount if order else 0,
                                                "paid_at": order.paid_at.strftime('%Y-%m-%d %H:%M:%S') if order and order.paid_at else datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                                            },
                                            order=order)
            else:
                return render_template_string(PAYMENT_RESULT_HTML,
                                            success=False,
                                            message=f"支付状态: {status}")
        
        # 加密模式（保留原有逻辑）
        encrypted_key = request.args.get("encrypted_key") or request.args.get("encrypted_data")
        iv = request.args.get("iv")
        ciphertext = request.args.get("ciphertext")
        
        if not all([encrypted_key, iv, ciphertext]):
            return render_template_string(PAYMENT_RESULT_HTML, 
                                        success=False, 
                                        message="缺少支付结果数据")
        
        # 处理支付结果
        result = PaymentService.handle_payment_result(encrypted_key, iv, ciphertext)
        
        if result["success"]:
            return render_template_string(PAYMENT_RESULT_HTML,
                                        success=True,
                                        message="支付成功",
                                        data=result["data"],
                                        order=result.get("order"))
        else:
            return render_template_string(PAYMENT_RESULT_HTML,
                                        success=False,
                                        message=result["message"])
    
    except Exception as e:
        return render_template_string(PAYMENT_RESULT_HTML,
                                    success=False,
                                    message=f"系统错误: {str(e)}")


@pay_bp.route("/callback", methods=["POST"])
def payment_callback():
    """
    银行异步回调接口
    接收加密数据，更新订单状态
    """
    try:
        data = request.get_json()
        
        # 【调试模式】直接接收简单JSON
        order_id = data.get("order_id")
        transaction_id = data.get("transaction_id")
        amount = data.get("amount")
        status = data.get("status")
        
        if not all([order_id, transaction_id]):
            return jsonify({"success": False, "message": "缺少必要参数"}), 400
        
        # 处理回调
        result = PaymentService.process_callback_simple(
            order_id=order_id,
            transaction_id=transaction_id,
            amount=amount,
            status=status
        )
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        return jsonify({"success": False, "message": f"回调处理失败: {str(e)}"}), 500


PAYMENT_RESULT_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>支付结果</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .result-container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            max-width: 500px;
            width: 90%;
            text-align: center;
        }
        .icon {
            font-size: 80px;
            margin-bottom: 20px;
        }
        .success .icon { color: #28a745; }
        .failure .icon { color: #dc3545; }
        h2 {
            margin-bottom: 20px;
            color: #333;
        }
        .message {
            color: #666;
            margin-bottom: 30px;
            font-size: 16px;
        }
        .details {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
            text-align: left;
        }
        .detail-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding: 8px 0;
            border-bottom: 1px solid #e0e0e0;
        }
        .detail-row:last-child {
            border-bottom: none;
            margin-bottom: 0;
        }
        .label { color: #666; }
        .value { color: #333; font-weight: bold; }
        .btn {
            display: inline-block;
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 10px;
            font-weight: bold;
            transition: all 0.3s;
            margin: 5px;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        .countdown {
            color: #999;
            font-size: 14px;
            margin-top: 20px;
        }
    </style>
</head>
<body class="{{ 'success' if success else 'failure' }}">
    <div class="result-container">
        <div class="icon">{{ '✅' if success else '❌' }}</div>
        <h2>{{ '支付成功' if success else '支付失败' }}</h2>
        <p class="message">{{ message }}</p>
        
        {% if success and data %}
        <div class="details">
            <div class="detail-row">
                <span class="label">订单号：</span>
                <span class="value">{{ data.order_id }}</span>
            </div>
            <div class="detail-row">
                <span class="label">交易号：</span>
                <span class="value">{{ data.transaction_id }}</span>
            </div>
            <div class="detail-row">
                <span class="label">支付金额：</span>
                <span class="value">¥{{ "%.2f"|format(data.amount) }}</span>
            </div>
            <div class="detail-row">
                <span class="label">支付时间：</span>
                <span class="value">{{ data.paid_at }}</span>
            </div>
        </div>
        {% endif %}
        
        <div>
            <a href="http://localhost:8081/orders" class="btn">查看订单</a>
            <a href="http://localhost:8081/" class="btn">返回首页</a>
        </div>
        
        <div class="countdown">
            <span id="countdown">5</span> 秒后自动跳转到订单列表...
        </div>
    </div>
    
    <script>
        // 倒计时自动跳转
        let seconds = 5;
        const countdownEl = document.getElementById('countdown');
        
        const timer = setInterval(() => {
            seconds--;
            countdownEl.textContent = seconds;
            
            if (seconds <= 0) {
                clearInterval(timer);
                window.location.href = 'http://localhost:8081/orders';
            }
        }, 1000);
    </script>
</body>
</html>
"""