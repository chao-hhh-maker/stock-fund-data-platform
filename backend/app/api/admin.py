"""用户 / 角色 / 租户管理路由（模块6：用户权限与安全管理）。

仅管理员可用。提供用户 CRUD、角色权限调整、租户管理。
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.database import get_db
from app.core.security import hash_password
from app.models import Role, Tenant, User
from app.schemas import (
    AdminUserCreate,
    AdminUserOut,
    AdminUserUpdate,
    Message,
    RoleOut,
    RoleUpdate,
    TenantCreate,
    TenantOut,
)
from app.services import audit_service

router = APIRouter(prefix="/admin", tags=["系统管理"])


def _to_user_out(u: User) -> AdminUserOut:
    return AdminUserOut(
        id=u.id, username=u.username, full_name=u.full_name, role=u.role.name,
        is_active=u.is_active, department=u.department, tenant_id=u.tenant_id,
        tenant_name=u.tenant.name if u.tenant else None, created_at=u.created_at,
    )


# ---------- 用户 ----------
@router.get("/users", response_model=List[AdminUserOut], summary="用户列表")
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> List[AdminUserOut]:
    users = db.query(User).order_by(User.id).all()
    return [_to_user_out(u) for u in users]


@router.post("/users", response_model=AdminUserOut, summary="创建用户")
def create_user(
    payload: AdminUserCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_admin),
) -> AdminUserOut:
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    role = db.query(Role).filter(Role.name == payload.role_name).first()
    if not role:
        raise HTTPException(status_code=400, detail=f"角色不存在：{payload.role_name}")
    user = User(
        username=payload.username,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name or payload.username,
        role_id=role.id,
        department=payload.department,
        tenant_id=payload.tenant_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    audit_service.log_action(
        db, username=current.username, role=current.role.name, action="user_create",
        target=payload.username, detail=f"role={payload.role_name}",
    )
    return _to_user_out(user)


@router.patch("/users/{user_id}", response_model=AdminUserOut, summary="更新用户")
def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_admin),
) -> AdminUserOut:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if payload.password:
        user.hashed_password = hash_password(payload.password)
    if payload.role_name:
        role = db.query(Role).filter(Role.name == payload.role_name).first()
        if not role:
            raise HTTPException(status_code=400, detail=f"角色不存在：{payload.role_name}")
        user.role_id = role.id
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.department is not None:
        user.department = payload.department
    if payload.tenant_id is not None:
        user.tenant_id = payload.tenant_id
    if payload.is_active is not None:
        user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    audit_service.log_action(
        db, username=current.username, role=current.role.name, action="user_update",
        target=user.username,
    )
    return _to_user_out(user)


@router.delete("/users/{user_id}", response_model=Message, summary="删除用户")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_admin),
) -> Message:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == current.id:
        raise HTTPException(status_code=400, detail="不能删除当前登录用户")
    username = user.username
    db.delete(user)
    db.commit()
    audit_service.log_action(
        db, username=current.username, role=current.role.name, action="user_delete",
        target=username,
    )
    return Message(message="已删除")


# ---------- 角色 ----------
@router.get("/roles", response_model=List[RoleOut], summary="角色列表")
def list_roles(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> List[RoleOut]:
    return [RoleOut.model_validate(r) for r in db.query(Role).order_by(Role.id).all()]


@router.patch("/roles/{role_id}", response_model=RoleOut, summary="更新角色权限")
def update_role(
    role_id: int,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_admin),
) -> RoleOut:
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(role, k, v)
    db.commit()
    db.refresh(role)
    audit_service.log_action(
        db, username=current.username, role=current.role.name, action="role_update",
        target=role.name,
    )
    return RoleOut.model_validate(role)


# ---------- 租户 ----------
@router.get("/tenants", response_model=List[TenantOut], summary="租户列表")
def list_tenants(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> List[TenantOut]:
    return [TenantOut.model_validate(t) for t in db.query(Tenant).order_by(Tenant.id).all()]


@router.post("/tenants", response_model=TenantOut, summary="创建租户")
def create_tenant(
    payload: TenantCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_admin),
) -> TenantOut:
    if db.query(Tenant).filter(Tenant.code == payload.code).first():
        raise HTTPException(status_code=400, detail="租户编码已存在")
    tenant = Tenant(code=payload.code, name=payload.name, description=payload.description)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    audit_service.log_action(
        db, username=current.username, role=current.role.name, action="tenant_create",
        target=payload.code,
    )
    return TenantOut.model_validate(tenant)
