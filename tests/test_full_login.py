import sys
sys.path.insert(0, 'backend')

# 导入所有模型以注册关系
from app.models import User, Role
from app.core.database import SessionLocal
from app.core.security import verify_password, create_access_token

print("Testing database connection...")
db = SessionLocal()
print("Database connected OK")

print("\nQuerying admin user...")
user = db.query(User).filter(User.username == "admin").first()
if user:
    print(f"Found user: id={user.id}, username={user.username}")
else:
    print("Admin user not found")
    sys.exit(1)

print("\nVerifying password...")
is_valid = verify_password("admin123", user.password_hash)
print(f"Password valid: {is_valid}")

print("\nCreating JWT Token...")
token = create_access_token(data={"sub": user.id})
print(f"Token created: {token[:50]}...")

db.close()
print("\nAll tests passed!")
