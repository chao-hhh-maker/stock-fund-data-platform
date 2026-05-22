"""
统一响应格式模块
"""
from typing import Optional, Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T')


class Response(BaseModel, Generic[T]):
    """统一响应格式"""
    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")


class ErrorResponse(BaseModel):
    """错误响应格式"""
    code: int = Field(..., description="错误码")
    message: str = Field(..., description="错误消息")
    detail: Optional[str] = Field(default=None, description="详细信息")


# 错误码定义
class ErrorCode:
    """错误码常量"""
    # 成功
    SUCCESS = 200

    # 客户端错误 (400-499)
    BAD_REQUEST = 400           # 请求参数错误
    UNAUTHORIZED = 401          # 未认证或token无效
    FORBIDDEN = 403             # 权限不足
    NOT_FOUND = 404             # 资源不存在
    VALIDATION_ERROR = 422      # 数据验证失败

    # 服务器错误 (500-599)
    INTERNAL_ERROR = 500        # 服务器内部错误
    DATABASE_ERROR = 503        # 数据库错误


# 常见错误消息
ERROR_MESSAGES = {
    ErrorCode.BAD_REQUEST: "请求参数错误",
    ErrorCode.UNAUTHORIZED: "未授权访问，请先登录",
    ErrorCode.FORBIDDEN: "权限不足，无法执行此操作",
    ErrorCode.NOT_FOUND: "请求的资源不存在",
    ErrorCode.VALIDATION_ERROR: "数据验证失败",
    ErrorCode.INTERNAL_ERROR: "服务器内部错误",
    ErrorCode.DATABASE_ERROR: "数据库操作失败",
}
