import bcrypt

# 生成admin123的密码哈希
password = "admin123"
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
print(f"密码: {password}")
print(f"哈希: {hashed.decode('utf-8')}")
