"""
导入所有模型以确保SQLAlchemy关系能正确解析
"""
from app.models.user import User
from app.models.role import Role

__all__ = ["User", "Role"]
