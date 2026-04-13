import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_register():
    """测试注册功能"""
    print("\n=== 测试注册 ===")
    url = f"{BASE_URL}/api/v1/users"
    
    # 测试用例
    test_cases = [
        {"username": "testuser1", "password": "password123", "desc": "正常注册"},
        {"username": "ab", "password": "password123", "desc": "用户名太短(2字符)"},
        {"username": "testuser1", "password": "password123", "desc": "用户名已存在"},
        {"username": "test user", "password": "password123", "desc": "用户名含空格"},
        {"username": "", "password": "password123", "desc": "用户名为空"},
    ]
    
    for case in test_cases:
        print(f"\n测试: {case['desc']}")
        print(f"  请求: {case}")
        try:
            resp = requests.post(url, json={
                "username": case["username"],
                "password": case["password"]
            })
            print(f"  状态码: {resp.status_code}")
            print(f"  响应: {resp.json()}")
        except Exception as e:
            print(f"  错误: {e}")

def test_login():
    """测试登录功能"""
    print("\n\n=== 测试登录 ===")
    url = f"{BASE_URL}/api/v1/auth/login"
    
    # 先注册一个用户用于测试登录
    register_url = f"{BASE_URL}/api/v1/users"
    test_user = {"username": "logintest", "password": "testpass123"}
    requests.post(register_url, json=test_user)
    
    # 测试用例
    test_cases = [
        {"username": "logintest", "password": "testpass123", "desc": "正常登录"},
        {"username": "logintest", "password": "wrongpass", "desc": "密码错误"},
        {"username": "notexist", "password": "testpass123", "desc": "用户不存在"},
        {"username": "", "password": "testpass123", "desc": "用户名为空"},
    ]
    
    for case in test_cases:
        print(f"\n测试: {case['desc']}")
        print(f"  请求: {case}")
        try:
            resp = requests.post(url, json={
                "username": case["username"],
                "password": case["password"]
            })
            print(f"  状态码: {resp.status_code}")
            data = resp.json()
            print(f"  响应: {data}")
            if resp.status_code == 200 and "data" in data and "token" in data["data"]:
                print(f"  ✓ 登录成功，获取到token!")
        except Exception as e:
            print(f"  错误: {e}")

def test_cors():
    """测试CORS预检请求"""
    print("\n\n=== 测试CORS ===")
    url = f"{BASE_URL}/api/v1/auth/login"
    
    print("\n发送OPTIONS预检请求...")
    try:
        resp = requests.options(url, headers={
            "Origin": "http://localhost:8080",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type"
        })
        print(f"状态码: {resp.status_code}")
        print(f"响应头: {dict(resp.headers)}")
        if resp.status_code == 200:
            print("✓ CORS预检通过")
        else:
            print("✗ CORS预检失败")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("Flask API 测试脚本")
    print("=" * 50)
    
    test_register()
    test_login()
    test_cors()
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)
