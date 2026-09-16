from functools import wraps
from flask import request
from app.utils.response import api_response
from app.services.JWT_SM2_Utils import jwt_service


def jwt_required(f):
    """保护需要登录的接口：校验 Bearer JWT（SM2 签名）"""

    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer"):
            return api_response(401, "未提供令牌，请先登录")

        parts = auth_header.split()
        if len(parts) != 2:
            return api_response(401, "令牌格式错误，请重新登录")

        token = parts[1]
        try:
            payload = jwt_service.verify_token(token)
        except Exception:
            return api_response(401, "令牌无效或已过期，请重新登录")

        request.user_info = payload
        return f(*args, **kwargs)

    return wrapper


def mfa_token_required(f):
    """保护 TOTP 二步验证接口：仅接受登录第一步颁发的「待二次验证」短时令牌。

    该令牌由 auth 登录流程在密码校验通过后签发，载荷含 mfa='pending'，
    有效期短（默认 300s），用于完成 TOTP 绑定/验证/恢复码登录等受限操作，
    防止未通过密码校验者直接调用 MFA 接口。
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer"):
            return api_response(401, "未提供二次验证令牌")

        parts = auth_header.split()
        if len(parts) != 2:
            return api_response(401, "令牌格式错误")

        token = parts[1]
        try:
            payload = jwt_service.verify_token(token)
        except Exception:
            return api_response(401, "二次验证令牌无效或已过期")

        if payload.get("mfa") != "pending":
            return api_response(401, "令牌类型错误，非二次验证令牌")

        request.user_info = payload
        return f(*args, **kwargs)

    return wrapper
