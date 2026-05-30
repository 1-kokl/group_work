
import requests
import json

# 测试签发证书接口
url = "http://localhost:5000/api/cert/issue"
data = {
    "username": "1234567"  # 使用已存在的用户
}

print("=" * 70)
print("测试证书签发接口")
print("=" * 70)
print(f"\n请求 URL: {url}")
print(f"请求数据: {json.dumps(data, ensure_ascii=False)}")
print("\n发送请求...\n")

try:
    response = requests.post(url, json=data)
    
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    if response.status_code == 200:
        print("\n✅ 签发成功！")
    else:
        print(f"\n❌ 签发失败，状态码: {response.status_code}")
        
except Exception as e:
    print(f"\n❌ 请求失败: {e}")
    print("\n请确保后端服务正在运行（python run.py）")

print("\n" + "=" * 70)
