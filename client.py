import requests

url = "https://localhost"

try:
    # 正常校验，不关闭验证
    resp = requests.get(url)
    print(resp.text)
except Exception as e:
    print("❌ 报错了！")
    print(e)
