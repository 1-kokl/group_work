"""
模拟银行服务 - 独立支付系统
运行在 8080 端口
功能：接收电商支付请求、验签、模拟扣款、加密结果、同步跳转+异步回调
"""
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import sqlite3
import os
import time
import secrets
from datetime import datetime, timedelta
from gmssl.sm2 import CryptSM2, default_ecc_table
from gmssl.sm3 import sm3_hash as _gmssl_sm3_hash, bytes_to_list
from gmssl.sm4 import CryptSM4, SM4_ENCRYPT, SM4_DECRYPT
import base64
import json
import threading

app = Flask(__name__)
CORS(app)

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), "bank.db")

# 电商公钥配置（用于验证电商签名和加密结果）
ECOMMERCE_PUBLIC_KEY = ""

# 银行私钥（用于签名和解密）
BANK_PRIVATE_KEY = ""
BANK_PUBLIC_KEY = ""

# 防重放存储
PROCESSED_ORDERS = set()


def init_db():
    """初始化银行数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建交易记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            order_no TEXT UNIQUE NOT NULL,
            amount REAL NOT NULL,
            merchant_id TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            paid_at TIMESTAMP
        )
    """)
    
    # 创建防重放表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS replay_protection (
            order_no TEXT PRIMARY KEY,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ 银行数据库初始化成功")


def load_bank_keys():
    """加载银行密钥对"""
    global BANK_PRIVATE_KEY, BANK_PUBLIC_KEY
    
    key_file = os.path.join(os.path.dirname(__file__), "bank_sm2_key.txt")
    
    if os.path.exists(key_file):
        with open(key_file, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f.read().strip().split("\n") if ln.strip()]
        if len(lines) >= 2:
            BANK_PRIVATE_KEY = lines[0]
            BANK_PUBLIC_KEY = lines[1]
            print(f"✅ 已加载银行密钥对")
            print(f"   公钥: {BANK_PUBLIC_KEY[:50]}...")
            return
    
    # 生成新密钥对
    para = len(default_ecc_table["n"])
    private_key = secrets.token_hex(32)
    placeholder = "0" * (2 * para)
    tmp = CryptSM2(private_key=private_key, public_key=placeholder)
    public_key = tmp._kg(int(private_key, 16), tmp.ecc_table["g"])
    
    BANK_PRIVATE_KEY = private_key
    BANK_PUBLIC_KEY = public_key
    
    with open(key_file, "w", encoding="utf-8") as f:
        f.write(f"{private_key}\n{public_key}\n")
    
    print("✅ 已生成并保存银行密钥对")
    print(f"   公钥: {public_key[:50]}...")


def load_ecommerce_public_key():
    """加载电商公钥（从电商系统的sm2_key.txt读取）"""
    global ECOMMERCE_PUBLIC_KEY
    
    # 尝试多个可能的路径
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "sm2_key.txt"),
        os.path.join(os.path.dirname(__file__), "app", "sm2_key.txt"),
        "sm2_key.txt"
    ]
    
    for key_file in possible_paths:
        if os.path.exists(key_file):
            try:
                with open(key_file, "r", encoding="utf-8") as f:
                    lines = [ln.strip() for ln in f.read().strip().split("\n") if ln.strip()]
                if len(lines) >= 2:
                    ECOMMERCE_PUBLIC_KEY = lines[1]  # 第二行是公钥
                    print(f"✅ 已加载电商公钥: {ECOMMERCE_PUBLIC_KEY[:50]}...")
                    return
            except Exception as e:
                print(f"⚠️ 读取 {key_file} 失败: {e}")
    
    print("⚠️ 未找到电商公钥文件，将跳过签名验证")


def sm3_hash(data):
    """SM3 哈希"""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return _gmssl_sm3_hash(bytes_to_list(data))


def verify_signature(order_id, amount, merchant_id, timestamp, signature):
    """
    验证电商签名 - 严格的SM2+SM3验证
    【生产模式】：启用完整的数字签名验证
    """
    try:
        print(f"🔐 [生产模式] 开始签名验证: order_id={order_id}")
        print(f"   待签名字符串: {order_id}|{amount}|{merchant_id}|{timestamp}")

        # 参数校验
        if not all([order_id, amount, merchant_id, timestamp, signature]):
            print("❌ 签名验证失败: 缺少必要参数")
            return False

        # 1. 构造待签名字符串
        sign_str = f"{order_id}|{amount}|{merchant_id}|{timestamp}"

        # 2. 计算SM3哈希
        expected_hash = sm3_hash(sign_str)
        print(f"   预期哈希值: {expected_hash[:64]}...")

        # 3. 使用电商公钥验证SM2签名
        if not ECOMMERCE_PUBLIC_KEY:
            print("⚠️  警告: 未配置电商公钥，无法进行严格验证")
            print("   请确保已加载电商系统的公钥")
            return False

        para = len(default_ecc_table["n"])
        placeholder = "0" * (2 * para)

        # 创建SM2验签对象（使用电商公钥）
        sm2 = CryptSM2(private_key="", public_key=ECOMMERCE_PUBLIC_KEY.lstrip("04"), mode=1)

        # 4. 验证签名
        is_valid = sm2.verify(expected_hash.encode("utf-8"), signature)

        if is_valid:
            print("✅ 签名验证通过 - 数据完整性确认")
            return True
        else:
            print("❌ 签名验证失败 - 数据可能被篡改")
            print(f"   可能原因:")
            print(f"   - 金额参数被修改")
            print(f"   - 订单号被篡改")
            print(f"   - 时间戳被伪造")
            print(f"   - 签名是伪造的")
            return False

    except Exception as e:
        print(f"❌ 签名验证异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def encrypt_with_digital_envelope(result_data):
    """
    数字信封加密：
    1. 随机生成 SM4 密钥
    2. 用 SM4 加密结果数据
    3. 用电商公钥（SM2）加密 SM4 密钥
    4. 返回（加密的SM4密钥 + IV + 密文）
    """
    try:
        # 1. 生成随机 SM4 密钥（16字节）
        sm4_key = secrets.token_bytes(16)
        iv = secrets.token_bytes(16)
        
        # 2. SM4 加密结果数据（CBC模式 + PKCS7填充）
        result_json = json.dumps(result_data, ensure_ascii=False).encode("utf-8")
        
        # PKCS7 填充
        block_size = 16
        padding_len = block_size - (len(result_json) % block_size)
        padded_data = result_json + bytes([padding_len] * padding_len)
        
        sm4 = CryptSM4()
        sm4.set_key(sm4_key, SM4_ENCRYPT)
        ciphertext = sm4.crypt_cbc(iv, padded_data)
        
        # 3. SM2 加密 SM4 密钥（使用电商公钥）
        if not ECOMMERCE_PUBLIC_KEY:
            raise ValueError("未配置电商公钥，无法加密")
        
        para = len(default_ecc_table["n"])
        sm2 = CryptSM2(private_key="", public_key=ECOMMERCE_PUBLIC_KEY.lstrip("04"), mode=1)
        
        encrypted_sm4_key = sm2.encrypt(sm4_key)
        
        # 4. 组装返回数据（全部转 hex 字符串）
        envelope = {
            "encrypted_key": encrypted_sm4_key.hex() if isinstance(encrypted_sm4_key, bytes) else encrypted_sm4_key,
            "iv": iv.hex(),
            "ciphertext": ciphertext.hex()
        }
        
        print("✅ 数字信封加密成功")
        return envelope
    except Exception as e:
        print(f"❌ 数字信封加密失败: {e}")
        import traceback
        traceback.print_exc()
        raise


def is_timestamp_valid(timestamp, validity_minutes=5):
    """校验时间戳是否在有效期内（默认5分钟）"""
    current_time = int(time.time())
    time_diff = abs(current_time - timestamp)
    return time_diff <= (validity_minutes * 60)


def is_order_processed(order_no):
    """检查订单是否已处理（防重放）"""
    print(f"🔍 [DEBUG] 检查订单是否已处理: {order_no}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM replay_protection WHERE order_no = ?", (order_no,))
    result = cursor.fetchone()
    conn.close()

    if result:
        print(f"   ✅ 订单已存在（应拦截）")
    else:
        print(f"   ❌ 订单不存在（允许通过）")

    return result is not None


def mark_order_processed(order_no):
    """标记订单已处理"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO replay_protection (order_no) VALUES (?)", (order_no,))
    conn.commit()
    conn.close()


PAYMENT_PAGE_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>模拟银行 - 支付确认</title>
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
        .payment-container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            max-width: 500px;
            width: 90%;
        }
        .bank-logo {
            text-align: center;
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 30px;
        }
        .order-info {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
        }
        .order-info h3 {
            color: #333;
            margin-bottom: 15px;
            font-size: 18px;
        }
        .info-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding: 8px 0;
            border-bottom: 1px solid #e0e0e0;
        }
        .info-row:last-child {
            border-bottom: none;
            margin-bottom: 0;
        }
        .info-label {
            color: #666;
            font-size: 14px;
        }
        .info-value {
            color: #333;
            font-weight: bold;
            font-size: 14px;
        }
        .amount {
            font-size: 24px;
            color: #ff6b6b;
        }
        .password-section {
            background: #fff3cd;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .password-section h4 {
            color: #856404;
            margin-bottom: 15px;
            font-size: 16px;
        }
        .password-input {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 18px;
            letter-spacing: 8px;
            text-align: center;
            margin-bottom: 10px;
        }
        .password-input:focus {
            outline: none;
            border-color: #667eea;
        }
        .password-hint {
            color: #856404;
            font-size: 12px;
            text-align: center;
        }
        .btn-group {
            display: flex;
            gap: 15px;
            margin-top: 30px;
        }
        .btn {
            flex: 1;
            padding: 15px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        .btn-confirm {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-confirm:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        .btn-cancel {
            background: #e0e0e0;
            color: #666;
        }
        .btn-cancel:hover {
            background: #d0d0d0;
        }
        .security-badge {
            text-align: center;
            margin-top: 20px;
            color: #28a745;
            font-size: 12px;
        }
        .error-message {
            background: #fee;
            color: #c33;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        .loading.show {
            display: block;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="payment-container">
        <div class="bank-logo">🏦 模拟银行支付网关</div>
        
        {% if error %}
        <div class="error-message">{{ error }}</div>
        {% else %}
        <div class="order-info">
            <h3>📋 订单信息</h3>
            <div class="info-row">
                <span class="info-label">订单号：</span>
                <span class="info-value">{{ order_id }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">商户编号：</span>
                <span class="info-value">{{ merchant_id }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">支付金额：</span>
                <span class="info-value amount">¥{{ "%.2f"|format(amount) }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">订单时间：</span>
                <span class="info-value">{{ timestamp|datetime_format }}</span>
            </div>
        </div>
        
        <form method="POST" action="/pay/process" id="paymentForm">
            <input type="hidden" name="order_id" value="{{ order_id }}">
            <input type="hidden" name="amount" value="{{ amount }}">
            <input type="hidden" name="merchant_id" value="{{ merchant_id }}">
            <input type="hidden" name="timestamp" value="{{ timestamp }}">
            <input type="hidden" name="signature" value="{{ signature }}">
            <input type="hidden" name="callback_url" value="{{ callback_url }}">
            
            <div class="password-section">
                <h4>🔐 请输入支付密码</h4>
                <input 
                    type="password" 
                    name="password" 
                    class="password-input" 
                    placeholder="******"
                    maxlength="6"
                    pattern="[0-9]{6}"
                    required
                    autofocus
                >
                <p class="password-hint">提示：任意6位数字即可（测试环境）</p>
            </div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>正在处理支付...</p>
            </div>
            
            <div class="btn-group" id="btnGroup">
                <button type="button" class="btn btn-cancel" onclick="cancelPayment()">取消支付</button>
                <button type="submit" class="btn btn-confirm">确认支付</button>
            </div>
        </form>
        
        <div class="security-badge">
            🔒 本交易采用国密SM2/SM3/SM4加密保护
        </div>
        {% endif %}
    </div>
    
    <script>
        const form = document.getElementById('paymentForm');
        const loading = document.getElementById('loading');
        const btnGroup = document.getElementById('btnGroup');
        
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const password = this.querySelector('input[name="password"]').value;
            
            if (password.length !== 6) {
                alert('请输入6位数字密码');
                return;
            }
            
            // 显示加载状态
            loading.classList.add('show');
            btnGroup.style.display = 'none';
            
            // 模拟处理延迟
            setTimeout(() => {
                form.submit();
            }, 1500);
        });
        
        function cancelPayment() {
            if (confirm('确定要取消支付吗？')) {
                window.location.href = 'http://localhost:8088/orders';
            }
        }
    </script>
</body>
</html>
"""


@app.route("/pay", methods=["GET"])
def pay_page():
    """
    银行支付页面
    接收参数：order_id, amount, merchant_id, timestamp, signature, callback_url
    """
    try:
        # 获取参数
        order_id = request.args.get("order_id")
        amount = request.args.get("amount", type=float)
        merchant_id = request.args.get("merchant_id")
        timestamp = request.args.get("timestamp", type=int)
        signature = request.args.get("signature")
        callback_url = request.args.get("callback_url", "http://localhost:5000/api/pay/result")

        # 参数校验
        if not all([order_id, amount, merchant_id, timestamp, signature]):
            return render_template_string(PAYMENT_PAGE_HTML,
                                          error="缺少必要参数",
                                          callback_url=callback_url)

        # 【第一道防线】时间戳校验（防重放）- 必须在最前面
        if not is_timestamp_valid(timestamp, validity_minutes=5):
            print(f"⏰ 请求被拒绝: 时间戳过期")
            print(f"   订单号: {order_id}")
            print(f"   请求时间戳: {timestamp}")
            print(f"   当前时间戳: {int(time.time())}")
            return render_template_string(PAYMENT_PAGE_HTML,
                                          error="请求已过期，请重新发起支付",
                                          callback_url=callback_url)

        # 【第二道防线】订单是否已处理（防重放）- 在签名验证之前
        if is_order_processed(order_id):
            print(f"🚫 请求被拒绝: 订单已处理（重放攻击）")
            print(f"   订单号: {order_id}")
            print(f"   这是第N次尝试处理该订单")
            return render_template_string(PAYMENT_PAGE_HTML,
                                          error="该订单已处理，请勿重复提交",
                                          callback_url=callback_url)

        # 【第三道防线】验证签名（防篡改）
        if not verify_signature(order_id, amount, merchant_id, timestamp, signature):
            print(f"❌ 请求被拒绝: 签名验证失败")
            print(f"   订单号: {order_id}")
            print(f"   金额: {amount}")
            return render_template_string(PAYMENT_PAGE_HTML,
                                          error="签名验证失败，可能存在数据篡改",
                                          callback_url=callback_url)

        # 渲染支付页面
        print(f"✅ 所有安全检查通过，显示支付页面")
        return render_template_string(PAYMENT_PAGE_HTML,
                                      order_id=order_id,
                                      amount=amount,
                                      merchant_id=merchant_id,
                                      timestamp=timestamp,
                                      signature=signature,
                                      callback_url=callback_url,
                                      error=None)

    except Exception as e:
        print(f"❌ 支付页面异常: {e}")
        import traceback
        traceback.print_exc()
        return render_template_string(PAYMENT_PAGE_HTML,
                                      error=f"系统错误: {str(e)}",
                                      callback_url=request.args.get("callback_url", ""))


@app.route("/pay/process", methods=["POST"])
def process_payment():
    """
    处理支付请求
    1. 验证密码
    2. 再次验签
    3. 防重放检查
    4. 模拟扣款
    5. 异步回调通知
    6. 同步跳转回电商
    """
    try:
        # 获取表单数据
        order_id = request.form.get("order_id")
        amount = request.form.get("amount", type=float)
        merchant_id = request.form.get("merchant_id")
        timestamp = request.form.get("timestamp", type=int)
        signature = request.form.get("signature")
        callback_url = request.form.get("callback_url", "http://localhost:5000/api/pay/result")
        password = request.form.get("password")
        
        # 参数校验
        if not all([order_id, amount, merchant_id, timestamp, signature]):
            return jsonify({"success": False, "message": "缺少必要参数"}), 400
        
        # 验证密码（简单验证：6位数字）
        if not password or len(password) != 6 or not password.isdigit():
            return render_template_string(PAYMENT_PAGE_HTML,
                                        order_id=order_id,
                                        amount=amount,
                                        merchant_id=merchant_id,
                                        timestamp=timestamp,
                                        signature=signature,
                                        callback_url=callback_url,
                                        error="支付密码格式错误，请输入6位数字")
        
        # 再次验签
        if not verify_signature(order_id, amount, merchant_id, timestamp, signature):
            return jsonify({"success": False, "message": "签名验证失败"}), 403

        # 【关键】防重放检查 - 二次确认
        if is_order_processed(order_id):
            print(f"🚫 支付处理被拒绝: 订单已处理")
            return jsonify({"success": False, "message": "订单已处理"}), 409

        # 标记订单已处理 - 立即标记，在处理前
        mark_order_processed(order_id)
        print(f"✅ 订单已标记为已处理，防止并发重放")

        # 模拟扣款
        transaction_id = f"TXN{int(time.time())}{secrets.token_hex(4)}"
        
        # 保存交易记录
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (id, order_no, amount, merchant_id, timestamp, status, paid_at)
            VALUES (?, ?, ?, ?, ?, 'completed', ?)
        """, (transaction_id, order_id, amount, merchant_id, timestamp, datetime.utcnow()))
        conn.commit()
        conn.close()
        
        print(f"✅ 支付成功 - 订单: {order_id}, 交易号: {transaction_id}, 金额: {amount}")
        
        # 构造简单的支付结果 JSON
        payment_result = {
            "order_id": order_id,
            "transaction_id": transaction_id,
            "amount": amount,
            "status": "success"
        }
        
        # 异步回调：通知电商后端更新订单状态
        async_callback_url = callback_url.replace("/result", "/callback")
        thread = threading.Thread(
            target=async_callback_simple,
            args=(async_callback_url, payment_result, order_id)
        )
        thread.daemon = True
        thread.start()
        
        print(f"🔄 正在跳转到电商结果页: {callback_url}")
        
        # 同步跳转页面 - 使用 JavaScript 确保跳转
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>支付成功</title>
        </head>
        <body>
            <div style="text-align:center;padding:50px;font-family:'Microsoft YaHei',sans-serif;">
                <div style="font-size:80px;margin-bottom:20px;">✅</div>
                <h2 style="color:#28a745;">支付成功！</h2>
                <p style="font-size:18px;color:#666;margin:20px 0;">
                    订单号：{order_id}<br>
                    交易号：{transaction_id}<br>
                    金额：¥{amount:.2f}
                </p>
                <p style="color:#999;">正在跳转回电商平台...</p>
            </div>
            <script>
                // 立即跳转
                setTimeout(function() {{
                    window.location.href = "{callback_url}?status=success&order_id={order_id}";
                }}, 1000);
            </script>
        </body>
        </html>
        """
    
    except Exception as e:
        print(f"❌ 支付处理失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"支付处理失败: {str(e)}"}), 500


def async_callback(callback_url, encrypted_result, order_id):
    """
    异步回调通知电商系统
    """
    import requests
    
    try:
        print(f"📤 准备异步回调: {callback_url}")
        time.sleep(2)  # 延迟2秒，确保用户已跳转
        
        response = requests.post(
            callback_url,
            json=encrypted_result,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ 回调成功: {callback_url}, 响应: {response.text}")
        else:
            print(f"❌ 回调失败: {response.status_code}, 响应: {response.text}")
    except Exception as e:
        print(f"❌ 回调异常: {e}")
        import traceback
        traceback.print_exc()

def async_callback_simple(callback_url, result_data, order_id):
    """
    简化版异步回调：直接发送 JSON，不使用数字信封
    """
    import requests
    try:
        print(f"📤 正在异步回调电商: {callback_url}")
        time.sleep(1) # 稍微延迟一下
        
        response = requests.post(
            callback_url,
            json=result_data, # 直接发送 JSON
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"✅ 回调成功: {response.text}")
        else:
            print(f"❌ 回调失败: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"❌ 回调异常: {e}")
        
@app.route("/health", methods=["GET"])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "ok",
        "service": "mock-bank",
        "port": 8080,
        "timestamp": datetime.utcnow().isoformat()
    })


@app.template_filter('datetime_format')
def datetime_format(value):
    """格式化时间戳为可读时间"""
    try:
        dt = datetime.fromtimestamp(int(value))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return value


if __name__ == "__main__":
    print("=" * 60)
    print("🏦 模拟银行服务启动中...")
    print("=" * 60)
    
    init_db()
    load_bank_keys()
    load_ecommerce_public_key()
    
    print("\n📡 服务地址:")
    print("   银行服务: http://localhost:8080")
    print("   支付接口: http://localhost:8080/pay")
    print("   健康检查: http://localhost:8080/health")
    print("=" * 60)
    
    app.run(host="0.0.0.0", port=8080, debug=True)
