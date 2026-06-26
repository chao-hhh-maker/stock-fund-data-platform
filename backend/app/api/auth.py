"""认证路由：登录、获取当前用户。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.models import User
from app.schemas import LoginRequest, Token, UserOut
from app.services import audit_service, user_service

router = APIRouter(prefix="/auth", tags=["认证"])


def _issue_token(user: User) -> Token:
    token = create_access_token(subject=user.username, role=user.role.name)
    return Token(
        access_token=token,
        role=user.role.name,
        username=user.username,
        data_scope=user.role.data_scope,
        max_history_days=user.role.max_history_days,
        can_export=user.role.can_export,
        can_view_sensitive=user.role.can_view_sensitive,
    )


@router.post("/login", response_model=Token, summary="用户名密码登录")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> Token:
    user = user_service.authenticate(db, payload.username, payload.password)
    if not user:
        audit_service.log_action(
            db, username=payload.username, action="login_failed",
            detail="用户名或密码错误", ip=request.client.host if request.client else "",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
        )
    audit_service.log_action(
        db, username=user.username, role=user.role.name, action="login",
        ip=request.client.host if request.client else "",
    )
    return _issue_token(user)


@router.post("/token", response_model=Token, summary="OAuth2 表单登录（供 Swagger 授权）")
def login_oauth(
    form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
) -> Token:
    user = user_service.authenticate(db, form.username, form.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
        )
    return _issue_token(user)


@router.get("/me", response_model=UserOut, summary="获取当前登录用户")
def me(current: User = Depends(get_current_user)) -> UserOut:
    return UserOut(
        id=current.id,
        username=current.username,
        full_name=current.full_name,
        role=current.role.name,
        is_active=current.is_active,
        data_scope=current.role.data_scope,
        max_history_days=current.role.max_history_days,
        can_export=current.role.can_export,
        can_view_sensitive=current.role.can_view_sensitive,
        tenant_id=current.tenant_id,
        department=current.department,
    )

