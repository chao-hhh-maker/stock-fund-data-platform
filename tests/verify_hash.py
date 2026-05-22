import sys
sys.path.insert(0, 'backend')

from app.core.security import verify_password

# 测试init.sql中的密码哈希
hash_from_sql = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYILp92S.0i"
password = "admin123"

print(f"测试密码: {password}")
print(f"数据库中的哈希: {hash_from_sql}")
print(f"验证结果: {verify_password(password, hash_from_sql)}")
