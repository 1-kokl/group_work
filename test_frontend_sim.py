import requests
import json

BASE_URL = "http://127.0.0.1:5000"

print("=" * 50)
print("模拟前端请求测试")
print("=" * 50)

# 测试注册 - 使用你提供的数据
print("\n=== 测试注册 ===")
register_url = f"{BASE_URL}/api/v1/users"
register_data = {
    "username": "iopiop",
    "password": "@Lzy123456",
    "phone": "13322554455"
}
print(f"POST {register_url}")
print(f"数据: {json.dumps(register_data, ensure_ascii=False)}")

try:
    resp = requests.post(register_url, json=register_data)
    print(f"状态码: {resp.status_code}")
    print(f"响应: {resp.json()}")
    
    if resp.status_code == 200:
        print("注册成功!")
except Exception as e:
    print(f"错误: {e}")

# 测试登录 - 使用你提供的数据
print("\n=== 测试登录 ===")
login_url = f"{BASE_URL}/api/v1/auth/login"
login_data = {
    "username": "iopiop",
    "password": "@Lzy123456"
}
print(f"POST {login_url}")
print(f"数据: {json.dumps(login_data, ensure_ascii=False)}")

try:
    resp = requests.post(login_url, json=login_data)
    print(f"状态码: {resp.status_code}")
    result = resp.json()
    print(f"响应: {result}")
    
    if resp.status_code == 200 and "data" in result and "token" in result["data"]:
        print(f"登录成功! Token: {result['data']['token'][:50]}...")
except Exception as e:
    print(f"错误: {e}")

print("\n" + "=" * 50)
print("测试完成")
print("=" * 50)
