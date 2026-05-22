import requests
import json

# 测试登录接口
url = "http://localhost:8001/api/auth/login"
data = {
    "username": "admin",
    "password": "admin123"
}

print("测试登录接口...")
response = requests.post(url, json=data)
print(f"状态码: {response.status_code}")
print(f"响应文本: {response.text}")
try:
    print(f"响应JSON: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"解析JSON失败: {e}")
