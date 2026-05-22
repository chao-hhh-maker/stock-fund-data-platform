"""
认证相关API接口
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt

from app.core.database import get_db
from app.core.config import settings
from app.core.security import verify_password, create_access_token, decode_access_token
from app.core.response import Response, ErrorResponse, ErrorCode
from app.models.user import User
from app.models.role import Role
from app.schemas.auth import LoginRequest, TokenResponse, UserInfo

router = APIRouter(prefix="/api/auth", tags=["认证"])

# OAuth2密码流
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """获取当前登录用户(依赖注入)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        if payload is None:
            raise credentials_exception

        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已被禁用"
        )

    return user


@router.post("/login", response_model=Response[TokenResponse], summary="用户登录")
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    用户登录接口

    - **username**: 用户名
    - **password**: 密码

    返回JWT访问令牌
    """
    # 查询用户
    user = db.query(User).filter(User.username == login_data.username).first()

    # 验证用户是否存在
    if not user:
        return Response(
            code=ErrorCode.UNAUTHORIZED,
            message="用户名或密码错误",
            data=None
        )

    # 验证密码
    if not verify_password(login_data.password, user.password_hash):
        return Response(
            code=ErrorCode.UNAUTHORIZED,
            message="用户名或密码错误",
            data=None
        )

    # 检查用户是否激活
    if not user.is_active:
        return Response(
            code=ErrorCode.FORBIDDEN,
            message="用户账户已被禁用",
            data=None
        )

    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=access_token_expires
    )

    # 返回token
    token_response = TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    return Response(
        code=ErrorCode.SUCCESS,
        message="登录成功",
        data=token_response
    )


@router.get("/me", response_model=Response[UserInfo], summary="获取当前用户信息")
def get_me(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户的详细信息

    需要在请求头中携带有效的Bearer Token:
    Authorization: Bearer <token>
    """
    user_info = UserInfo(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role_name=current_user.role.role_name if current_user.role else None,
        is_active=current_user.is_active
    )

    return Response(
        code=ErrorCode.SUCCESS,
        message="获取用户信息成功",
        data=user_info
    )
