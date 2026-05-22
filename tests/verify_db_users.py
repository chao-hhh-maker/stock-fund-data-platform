import sys
sys.path.insert(0, 'backend')

from app.models import User, Role
from app.core.database import SessionLocal
from app.core.security import verify_password

print("=" * 60)
print("验证数据库和用户数据")
print("=" * 60)

db = SessionLocal()

try:
    # 检查角色
    print("\n1. 检查角色数据:")
    roles = db.query(Role).all()
    if roles:
        for role in roles:
            print(f"   - ID: {role.id}, 名称: {role.role_name}, 描述: {role.description}")
    else:
        print("   ✗ 没有找到角色数据")
    
    # 检查用户
    print("\n2. 检查用户数据:")
    users = db.query(User).all()
    if users:
        for user in users:
            role_name = user.role.role_name if user.role else "无角色"
            print(f"   - ID: {user.id}, 用户名: {user.username}, 邮箱: {user.email}, 角色: {role_name}, 激活: {user.is_active}")
            
            # 验证密码
            if user.username == "admin":
                is_valid = verify_password("admin123", user.password_hash)
                print(f"     密码验证 (admin123): {'✓ 正确' if is_valid else '✗ 错误'}")
    else:
        print("   ✗ 没有找到用户数据")
    
    print("\n✓ 数据库验证完成")
    
except Exception as e:
    print(f"\n✗ 验证失败: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

print("\n" + "=" * 60)
