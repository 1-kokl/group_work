"""测试用户注册接口"""
import requests
import json

# 测试注册接口
url = "http://localhost:5000/api/v1/users"

# 测试数据
test_data = {
    "username": "testuser123",
    "password": "Test1234.",
    "phone": "13800138000"
}

print("=" * 60)
print("🧪 测试用户注册接口")
print("=" * 60)

try:
    response = requests.post(url, json=test_data)
    print(f"\n状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"❌ 请求失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
