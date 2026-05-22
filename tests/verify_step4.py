"""
第四步完成验证脚本
测试所有核心接口功能
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8001"

def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_health_check():
    """测试健康检查接口"""
    print_section("测试 1: 健康检查接口")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
            print("✅ 健康检查接口正常")
            return True
        else:
            print(f"❌ 健康检查接口异常: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_login():
    """测试登录接口"""
    print_section("测试 2: 登录接口")
    
    # 测试正确密码
    print("\n2.1 测试正确密码登录:")
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        print(f"状态码: {response.status_code}")
        
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200 and result.get('code') == 200:
            print("✅ 登录成功")
            token = result['data']['access_token']
            print(f"Token (前50字符): {token[:50]}...")
            return token
        else:
            print("❌ 登录失败")
            return None
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None

def test_get_me(token):
    """测试获取用户信息接口"""
    print_section("测试 3: 获取用户信息接口")
    
    if not token:
        print("❌ 跳过测试：没有有效的 token")
        return False
    
    try:
        headers = {
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        print(f"状态码: {response.status_code}")
        
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200 and result.get('code') == 200:
            print("✅ 获取用户信息成功")
            return True
        else:
            print("❌ 获取用户信息失败")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_invalid_token():
    """测试无效 token"""
    print_section("测试 4: 无效 Token 访问")
    
    try:
        headers = {
            "Authorization": "Bearer invalid_token_here"
        }
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        print(f"状态码: {response.status_code}")
        
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if response.status_code == 401:
            print("✅ 无效 Token 被正确拒绝")
            return True
        else:
            print("❌ 无效 Token 未被正确拒绝")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_wrong_password():
    """测试错误密码"""
    print_section("测试 5: 错误密码登录")
    
    try:
        login_data = {
            "username": "admin",
            "password": "wrong_password"
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        print(f"状态码: {response.status_code}")
        
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200 and result.get('code') == 401:
            print("✅ 错误密码被正确拒绝")
            return True
        else:
            print("❌ 错误密码未被正确处理")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def main():
    print("\n" + "🚀" * 30)
    print("  第四步完成验证 - 后端认证与基础接口")
    print("🚀" * 30)
    
    results = []
    
    # 测试1: 健康检查
    results.append(("健康检查", test_health_check()))
    
    # 测试2: 登录
    token = test_login()
    results.append(("登录接口", token is not None))
    
    # 测试3: 获取用户信息
    results.append(("获取用户信息", test_get_me(token)))
    
    # 测试4: 无效 token
    results.append(("无效Token处理", test_invalid_token()))
    
    # 测试5: 错误密码
    results.append(("错误密码处理", test_wrong_password()))
    
    # 汇总结果
    print_section("测试结果汇总")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:20s} {status}")
    
    print("\n" + "-" * 60)
    print(f"总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！第四步已完成！")
        print("\n可以访问 Swagger 文档进行更多测试:")
        print(f"  http://{BASE_URL.replace('http://', '')}/docs")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查问题")
        return 1

if __name__ == "__main__":
    sys.exit(main())
