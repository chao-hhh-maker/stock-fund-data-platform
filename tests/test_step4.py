import requests
import json

base_url = "http://localhost:8001"

print("=" * 60)
print("测试第四步：后端最小闭环")
print("=" * 60)

# 测试1：健康检查接口
print("\n1. 测试健康检查接口 GET /api/health")
try:
    response = requests.get(f"{base_url}/api/health")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    if response.status_code == 200:
        print("   ✓ 健康检查接口正常")
    else:
        print("   ✗ 健康检查接口异常")
except Exception as e:
    print(f"   ✗ 请求失败: {e}")

# 测试2：登录接口
print("\n2. 测试登录接口 POST /api/auth/login")
try:
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    response = requests.post(f"{base_url}/api/auth/login", json=login_data)
    print(f"   状态码: {response.status_code}")
    result = response.json()
    print(f"   响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if response.status_code == 200 and result.get('code') == 200:
        print("   ✓ 登录成功")
        token = result['data']['access_token']
        print(f"   Token: {token[:50]}...")
    else:
        print("   ✗ 登录失败")
        token = None
except Exception as e:
    print(f"   ✗ 请求失败: {e}")
    token = None

# 测试3：获取当前用户信息
if token:
    print("\n3. 测试获取用户信息接口 GET /api/auth/me")
    try:
        headers = {
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(f"{base_url}/api/auth/me", headers=headers)
        print(f"   状态码: {response.status_code}")
        result = response.json()
        print(f"   响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200 and result.get('code') == 200:
            print("   ✓ 获取用户信息成功")
        else:
            print("   ✗ 获取用户信息失败")
    except Exception as e:
        print(f"   ✗ 请求失败: {e}")
else:
    print("\n3. 跳过获取用户信息测试（因为没有token）")

# 测试4：无效token测试
print("\n4. 测试无效Token访问受保护接口")
try:
    headers = {
        "Authorization": "Bearer invalid_token"
    }
    response = requests.get(f"{base_url}/api/auth/me", headers=headers)
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 401:
        print("   ✓ 无效Token被正确拒绝")
    else:
        print("   ✗ 无效Token未被正确拒绝")
except Exception as e:
    print(f"   ✗ 请求失败: {e}")

# 测试5：错误密码测试
print("\n5. 测试错误密码登录")
try:
    login_data = {
        "username": "admin",
        "password": "wrong_password"
    }
    response = requests.post(f"{base_url}/api/auth/login", json=login_data)
    print(f"   状态码: {response.status_code}")
    result = response.json()
    print(f"   响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if response.status_code == 200 and result.get('code') == 401:
        print("   ✓ 错误密码被正确拒绝")
    else:
        print("   ✗ 错误密码未被正确处理")
except Exception as e:
    print(f"   ✗ 请求失败: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
