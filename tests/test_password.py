"""
直接测试认证逻辑
"""
import sys
sys.path.insert(0, 'backend')

from app.core.security import verify_password

# 测试密码验证
hashed = "$2b$12$BmdEUWyKxK1DOUWolgaT6eCiZpPAc5rZS3j9XOXcTFsWZVDvngS0i"
password = "admin123"

result = verify_password(password, hashed)
print(f"密码验证结果: {result}")

if result:
    print("✅ 密码验证成功!")
else:
    print("❌ 密码验证失败!")
