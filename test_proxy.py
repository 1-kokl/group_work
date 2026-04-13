import requests

# 通过代理测试（即前端通过localhost:8080/api访问后端）
BASE_URL = "http://localhost:8080"

print("测试通过代理访问后端...")

# 测试注册
print("\n=== 通过代理测试注册 ===")
url = f"{BASE_URL}/api/v1/users"
data = {
    "username": "testproxy999",
    "password": "@Lzy123456",
    "phone": "13322554455"
}

try:
    resp = requests.post(url, json=data, timeout=10)
    print(f"状态码: {resp.status_code}")
    print(f"响应: {resp.json()}")
except Exception as e:
    print(f"错误: {e}")
