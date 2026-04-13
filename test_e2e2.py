import requests
import json

BASE_URL = "http://localhost:8080"

print("=" * 60)
print("完整端到端测试")
print("=" * 60)

# 使用新的测试数据
test_user = {
    "username": "newuser123",
    "email": "test@example.com",
    "password": "@Lzy123456",
    "phone": "13322554455"
}

# 1. 测试注册
print("\n【1】测试注册")
print(f"请求: POST /api/v1/users")
print(f"数据: {json.dumps(test_user, ensure_ascii=False)}")

try:
    resp = requests.post(f"{BASE_URL}/api/v1/users", json=test_user, timeout=10)
    print(f"状态码: {resp.status_code}")
    result = resp.json()
    print(f"响应: {result}")
    
    if resp.status_code == 200:
        print("[OK] 注册成功!")
    else:
        print(f"[FAIL] 注册失败: {result.get('msg')}")
except Exception as e:
    print(f"[FAIL] 请求失败: {e}")

# 2. 测试登录
print("\n【2】测试登录")
login_data = {
    "username": test_user["username"],
    "password": test_user["password"]
}
print(f"请求: POST /api/v1/auth/login")
print(f"数据: {json.dumps(login_data, ensure_ascii=False)}")

try:
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data, timeout=10)
    print(f"状态码: {resp.status_code}")
    result = resp.json()
    print(f"响应: {result}")
    
    if resp.status_code == 200 and result.get("code") == 200:
        token = result["data"]["token"]
        print(f"[OK] 登录成功! Token: {token[:50]}...")
    else:
        print(f"[FAIL] 登录失败")
except Exception as e:
    print(f"[FAIL] 请求失败: {e}")

# 3. 测试获取用户信息（需要token）
print("\n【3】测试获取用户信息（需要认证）")
headers = {"Authorization": f"Bearer {token}"} if 'token' in dir() else {}
try:
    resp = requests.get(f"{BASE_URL}/api/v1/user/info", headers=headers, timeout=10)
    print(f"状态码: {resp.status_code}")
    print(f"响应: {resp.json()}")
except Exception as e:
    print(f"[FAIL] 请求失败: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
