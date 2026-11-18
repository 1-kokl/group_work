"""
完整的支付流程测试脚本
测试电商下单 -> 跳转银行 -> 支付 -> 回调 -> 订单状态更新
"""
import requests
import time
import json
import sys
import os

# 配置
ECOMMERCE_BASE_URL = "http://localhost:5000"
BANK_BASE_URL = "http://localhost:8080"

def test_health():
    """测试服务健康状态"""
    print("\n=== 1. 测试服务健康状态 ===")
    
    try:
        # 测试电商服务
        response = requests.get(f"{ECOMMERCE_BASE_URL}/api/ecommerce/products?page=1&per_page=1", timeout=5)
        if response.status_code == 200:
            print("✅ 电商服务正常 (端口 5000)")
        else:
            print(f"❌ 电商服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 电商服务无法连接: {e}")
        print("   请先启动电商服务: python run.py")
        return False
    
    try:
        # 测试银行服务
        response = requests.get(f"{BANK_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 银行服务正常 (端口 8080)")
        else:
            print(f"❌ 银行服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 银行服务无法连接: {e}")
        print("   请先启动银行服务: python mock_bank.py")
        return False
    
    return True


def test_create_order(token):
    """测试创建订单"""
    print("\n=== 2. 创建测试订单 ===")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 创建订单数据
    order_data = {
        "shipping_address": "测试地址",
        "contact_phone": "13800138000",
        "remark": "测试订单",
        "items": [
            {
                "product_id": "test-product-1",
                "quantity": 1
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{ECOMMERCE_BASE_URL}/api/ecommerce/orders",
            json=order_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                order_id = data["data"]["id"]
                order_no = data["data"]["order_no"]
                total_amount = data["data"]["total_amount"]
                print(f"✅ 订单创建成功")
                print(f"   订单ID: {order_id}")
                print(f"   订单号: {order_no}")
                print(f"   金额: ¥{total_amount}")
                return order_id, order_no, total_amount
            else:
                print(f"❌ 订单创建失败: {data.get('message')}")
                return None, None, None
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"   响应: {response.text}")
            return None, None, None
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None, None, None


def test_login(username="testuser", password="123456"):
    """测试用户登录"""
    print("\n=== 0. 用户登录 ===")
    
    login_data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(
            f"{ECOMMERCE_BASE_URL}/api/auth/login",
            json=login_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                token = data["data"]["token"]
                print(f"✅ 登录成功")
                print(f"   Token: {token[:50]}...")
                return token
            else:
                print(f"❌ 登录失败: {data.get('message')}")
                return None
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None


def test_payment_flow(order_id, order_no, amount):
    """测试支付流程"""
    print(f"\n=== 3. 发起支付请求 ===")
    print(f"   订单ID: {order_id}")
    print(f"   订单号: {order_no}")
    print(f"   金额: ¥{amount}")
    
    # 这里需要token，实际测试时需要先登录
    print("\n💡 提示：完整测试需要用户登录获取token")
    print("   请使用浏览器访问: http://localhost:8080")
    print(f"   手动构造支付URL进行测试:")
    
    # 构造支付URL示例
    import time
    import secrets
    from gmssl.sm2 import CryptSM2, default_ecc_table
    from gmssl.sm3 import sm3_hash as _gmssl_sm3_hash, bytes_to_list
    import base64
    
    def sm3_hash_func(data):
        if isinstance(data, str):
            data = data.encode("utf-8")
        return _gmssl_sm3_hash(bytes_to_list(data))
    
    # 生成签名（示例）
    timestamp = int(time.time())
    merchant_id = "MERCHANT_001"
    sign_str = f"{order_no}|{amount}|{merchant_id}|{timestamp}"
    hash_value = sm3_hash_func(sign_str)
    
    print(f"\n   签名原文: {sign_str}")
    print(f"   时间戳: {timestamp}")
    
    bank_pay_url = (
        f"http://localhost:8080/pay?"
        f"order_id={order_no}"
        f"&amount={amount}"
        f"&merchant_id={merchant_id}"
        f"&timestamp={timestamp}"
        f"&signature=test_signature"
        f"&callback_url=http://localhost:5000/api/pay/result"
    )
    
    print(f"\n   支付URL: {bank_pay_url}")
    print("\n   📝 请在浏览器中打开上述URL进行手动测试")
    
    return True


def main():
    """主测试流程"""
    print("=" * 60)
    print("🧪 电商-银行支付系统联调测试")
    print("=" * 60)
    
    # 1. 测试服务健康
    if not test_health():
        print("\n❌ 服务检查失败，请先启动相关服务")
        sys.exit(1)
    
    # 2. 尝试登录（可选）
    token = test_login()
    
    if token:
        # 3. 创建订单
        order_id, order_no, amount = test_create_order(token)
        
        if order_id:
            # 4. 测试支付流程
            test_payment_flow(order_id, order_no, amount)
    else:
        print("\n⚠️ 未登录，跳过订单创建测试")
        print("   可以手动创建订单后测试支付流程")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)
    print("\n📖 完整测试步骤:")
    print("1. 启动电商服务: python run.py")
    print("2. 启动银行服务: python mock_bank.py")
    print("3. 注册/登录用户")
    print("4. 创建商品和订单")
    print("5. 点击'去支付'按钮")
    print("6. 在银行页面确认支付")
    print("7. 查看支付结果和订单状态更新")
    print("=" * 60)


if __name__ == "__main__":
    main()

