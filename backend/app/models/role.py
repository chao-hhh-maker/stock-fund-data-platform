"""
角色模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.core.database import Base


class Role(Base):
    """角色表模型"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True, comment="角色ID")
    role_name = Column(String(50), unique=True, nullable=False, index=True, comment="角色名称")
    description = Column(String(255), comment="角色描述")
    permissions = Column(Text, comment="权限列表(JSON格式)")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.role_name}')>"
