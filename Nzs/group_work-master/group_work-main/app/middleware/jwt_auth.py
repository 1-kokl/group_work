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
