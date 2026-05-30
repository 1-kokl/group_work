"""
支付流程测试脚本
测试：电商下单 -> 银行支付 -> 回调更新订单
"""
import requests
import time
import json

# 配置
ECOMMERCE_BASE_URL = "http://localhost:5000"
BANK_BASE_URL = "http://localhost:8080"

def test_payment_flow():
    """完整支付流程测试"""
    print("=" * 60)
    print("🧪 开始测试支付流程")
    print("=" * 60)
    
    # Step 1: 登录获取Token
    print("\n📝 Step 1: 用户登录...")
    login_response = requests.post(
        f"{ECOMMERCE_BASE_URL}/api/v1/auth/login",
        json={"username": "testuser", "password": "TestPass123!"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ 登录失败: {login_response.text}")
        return
    
    token_data = login_response.json()
    access_token = (
        token_data.get("data", {}).get("access_token") or 
        token_data.get("data", {}).get("token") or 
        token_data.get("access_token") or 
        token_data.get("token")
    )
    
    if not access_token:
        print(f"❌ 未获取到Token: {token_data}")
        return
    
    print("✅ 登录成功")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Step 2: 创建商品（如果不存在）
    print("\n📦 Step 2: 创建测试商品...")
    product_response = requests.post(
        f"{ECOMMERCE_BASE_URL}/api/ecommerce/products",
        json={
            "name": "测试商品",
            "price": 99.99,
            "stock": 100,
            "description": "支付测试商品"
        },
        headers=headers
    )
    print(f"   [DEBUG] 状态码: {product_response.status_code}")
    print(f"   [DEBUG] 响应内容: {product_response.text}")
    print(f"   [DEBUG] 请求头: {headers}")
    if product_response.status_code in [201, 200]:
        try:
            product_data = product_response.json()
            product_id = product_data.get("data", {}).get("id")
            print(f"✅ 商品创建成功: {product_id}")
        except Exception as e:
            print(f"⚠️ 解析商品响应失败: {e}")
            print(f"   响应内容: {product_response.text[:200]}")
            product_id = None
    else:
        print(f"⚠️ 商品创建失败（状态码: {product_response.status_code}），尝试使用已有商品")
        product_id = None
    
    # 如果没有创建成功，尝试获取已有商品
    if not product_id:
        try:
            products_response = requests.get(f"{ECOMMERCE_BASE_URL}/api/ecommerce/products?page=1&per_page=1")
            print(f"   商品列表响应状态: {products_response.status_code}")
            
            if products_response.status_code == 200:
                products_data = products_response.json()
                items = products_data.get("data", {}).get("items", [])
                if items:
                    product_id = items[0]["id"]
                    print(f"✅ 使用已有商品: {product_id}")
                else:
                    print("❌ 没有可用商品，请先手动创建商品")
                    return
            else:
                print(f"❌ 获取商品列表失败: {products_response.text[:200]}")
                return
        except Exception as e:
            print(f"❌ 获取商品异常: {e}")
            print(f"   响应内容: {products_response.text[:200] if 'products_response' in locals() else 'N/A'}")
            return

    # Step 3: 添加到购物车
    print("\n🛒 Step 3: 添加到购物车...")
    cart_response = requests.post(
        f"{ECOMMERCE_BASE_URL}/api/ecommerce/cart",
        json={"product_id": product_id, "quantity": 1},
        headers=headers
    )
    
    if cart_response.status_code == 200:
        print("✅ 添加到购物车成功")
    else:
        print(f"❌ 添加到购物车失败: {cart_response.text}")
        return
    
    # Step 4: 创建订单
    print("\n📋 Step 4: 创建订单...")
    order_response = requests.post(
        f"{ECOMMERCE_BASE_URL}/api/ecommerce/orders",
        json={
            "shipping_address": "测试地址",
            "contact_phone": "13800138000",
            "remark": "支付测试订单"
        },
        headers=headers
    )
    
    if order_response.status_code != 201:
        print(f"❌ 创建订单失败: {order_response.text}")
        return
    
    order_data = order_response.json()
    order_id = order_data["data"]["id"]
    order_no = order_data["data"]["order_no"]
    total_amount = order_data["data"]["total_amount"]
    
    print(f"✅ 订单创建成功")
    print(f"   订单ID: {order_id}")
    print(f"   订单号: {order_no}")
    print(f"   金额: ¥{total_amount}")
    
    # Step 5: 创建支付请求
    print("\n💳 Step 5: 创建支付请求...")
    payment_response = requests.post(
        f"{ECOMMERCE_BASE_URL}/api/pay/create/{order_id}",
        headers=headers
    )
    
    if payment_response.status_code != 200:
        print(f"❌ 创建支付失败: {payment_response.text}")
        return
    
    payment_data = payment_response.json()
    payment_url = payment_data["data"]["payment_url"]
    
    print(f"✅ 支付请求创建成功")
    print(f"   支付URL: {payment_url[:100]}...")
    
    # Step 6: 模拟浏览器跳转到银行（这里用API调用模拟）
    print("\n🏦 Step 6: 访问银行支付页面...")
    bank_response = requests.get(payment_url)
    
    if bank_response.status_code == 200:
        print("✅ 银行支付页面加载成功")
    else:
        print(f"⚠️ 银行页面访问异常: {bank_response.status_code}")
    
    # Step 7: 模拟在银行页面确认支付
    print("\n✅ Step 7: 确认支付...")
    
    # 提取表单参数
    import re
    form_data = {
        "order_id": order_no,
        "amount": total_amount,
        "merchant_id": "MERCHANT_001",
        "timestamp": payment_data["data"]["timestamp"],
        "signature": payment_data["data"]["signature"],
        "callback_url": "http://localhost:5000/api/pay/callback"
    }
    
    process_response = requests.post(
        f"{BANK_BASE_URL}/pay/process",
        data=form_data
    )
    
    if process_response.status_code == 200:
        print("✅ 银行处理支付成功")
        print(f"   响应: {process_response.text[:200]}")
    else:
        print(f"⚠️ 银行处理异常: {process_response.status_code}")
    
        # Step 8: 等待并手动触发回调
    print("\n⏳ Step 8: 等待异步回调...")
    time.sleep(2)
    
    # 【关键修正】确保这里使用的 order_no 或 order_id 与创建订单时的一致
    # 注意：有些系统回调用 order_no (字符串)，有些用 order_id (UUID)
    # 我们的 pay_routes.py 里写的是 data.get('order_id')
    # 所以这里必须传 order_id
    
    print(f"\n🔄 正在手动触发回调，目标订单ID: {order_id}")
    
    callback_data = {
        "order_id": order_id,      # <--- 确保这里是 Step 4 拿到的 order_id
        "transaction_id": "TXN_MOCK_123",
        "amount": total_amount,
        "status": "success"
    }
    
    try:
        callback_response = requests.post(
            f"{ECOMMERCE_BASE_URL}/api/pay/callback",
            json=callback_data,
            headers=headers
        )
        
        print(f"   回调响应状态码: {callback_response.status_code}")
        print(f"   回调响应内容: {callback_response.text}")
        
        if callback_response.status_code == 200:
            print("   ✅ 回调接口调用成功！")
        else:
            print("   ❌ 回调接口调用失败，请检查后端日志")
            
    except Exception as e:
        print(f"   ❌ 回调请求异常: {e}")

    # Step 9: 查询订单支付状态...
    print("\n🔍 Step 9: 查询订单支付状态...")
    order_status_response = requests.get(
       f"{ECOMMERCE_BASE_URL}/api/ecommerce/orders/{order_id}",
       headers=headers
    )
    
    if order_status_response.status_code == 200:
        order_status = order_status_response.json()
        payment_status = order_status["data"].get("payment_status")
        status = order_status["data"].get("status")
        transaction_id = order_status["data"].get("transaction_id")
        
        print(f"✅ 订单状态查询成功")
        print(f"   支付状态: {payment_status}")
        print(f"   订单状态: {status}")
        print(f"   交易号: {transaction_id}")
        
        if payment_status == "paid":
            print("\n🎉 支付流程测试成功！")
        else:
            print(f"\n⚠️ 支付状态未更新为 'paid'，当前状态: {payment_status}")
    else:
        print(f"❌ 查询订单状态失败: {order_status_response.text}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_payment_flow()
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()