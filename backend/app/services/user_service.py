"""用户与认证服务。"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models import Role, Tenant, User


def get_or_create_role(
    db: Session,
    name: str,
    description: str = "",
    *,
    data_scope: str = "all",
    max_history_days: int = 0,
    can_export: bool = True,
    can_view_sensitive: bool = False,
) -> Role:
    role = db.query(Role).filter(Role.name == name).first()
    if not role:
        role = Role(
            name=name,
            description=description,
            data_scope=data_scope,
            max_history_days=max_history_days,
            can_export=can_export,
            can_view_sensitive=can_view_sensitive,
        )
        db.add(role)
        db.commit()
        db.refresh(role)
    return role


def get_or_create_tenant(db: Session, code: str, name: str, description: str = "") -> Tenant:
    tenant = db.query(Tenant).filter(Tenant.code == code).first()
    if not tenant:
        tenant = Tenant(code=code, name=name, description=description)
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    return tenant


def authenticate(db: Session, username: str, password: str) -> Optional[User]:
    """校验用户名密码，成功返回用户。"""
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_user(
    db: Session,
    username: str,
    password: str,
    role_name: str,
    full_name: str = "",
    tenant_id: Optional[int] = None,
    department: str = "",
) -> User:
    role = get_or_create_role(db, role_name)
    user = User(
        username=username,
        hashed_password=hash_password(password),
        role_id=role.id,
        full_name=full_name or username,
        tenant_id=tenant_id,
        department=department,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def ensure_seed_users(db: Session, settings) -> None:
    """首次启动时创建默认租户、角色与管理员 / 普通用户。"""
    # 默认租户（机构级隔离基座）
    default_tenant = get_or_create_tenant(db, "HQ", "总部", "系统默认机构")
    research_tenant = get_or_create_tenant(db, "RESEARCH", "研究部", "演示部门级隔离")

    # 角色：admin 全权限；viewer 受限（不可见敏感字段、可导出）；analyst 仅股票+近一年（演示行级/时间权限）
    get_or_create_role(
        db, "admin", "管理员：可采集、导出、管理任务与用户",
        data_scope="all", max_history_days=0, can_export=True, can_view_sensitive=True,
    )
    get_or_create_role(
        db, "viewer", "普通用户：仅可查询与查看（敏感字段脱敏）",
        data_scope="all", max_history_days=0, can_export=True, can_view_sensitive=False,
    )
    get_or_create_role(
        db, "analyst", "研究员：仅股票数据、近 365 天、不可导出（演示行级/时间权限）",
        data_scope="stock", max_history_days=365, can_export=False, can_view_sensitive=False,
    )

    admin_role = db.query(Role).filter(Role.name == "admin").first()

    if not db.query(User).filter(User.username == settings.FIRST_ADMIN_USERNAME).first():
        create_user(
            db, settings.FIRST_ADMIN_USERNAME, settings.FIRST_ADMIN_PASSWORD,
            "admin", "系统管理员", tenant_id=default_tenant.id, department="信息技术部",
        )
    else:
        # 兼容旧库：补齐管理员的租户/敏感字段权限
        admin = db.query(User).filter(User.username == settings.FIRST_ADMIN_USERNAME).first()
        if admin and admin.tenant_id is None:
            admin.tenant_id = default_tenant.id
            db.commit()
    if admin_role and not admin_role.can_view_sensitive:
        admin_role.can_view_sensitive = True
        admin_role.data_scope = "all"
        db.commit()

    if not db.query(User).filter(User.username == settings.FIRST_USER_USERNAME).first():
        create_user(
            db, settings.FIRST_USER_USERNAME, settings.FIRST_USER_PASSWORD,
            "viewer", "演示用户", tenant_id=default_tenant.id, department="市场部",
        )
    # 演示研究员账号（行级 + 时间权限）
    if not db.query(User).filter(User.username == "analyst").first():
        create_user(
            db, "analyst", "analyst123",
            "analyst", "研究员", tenant_id=research_tenant.id, department="研究部",
        )
