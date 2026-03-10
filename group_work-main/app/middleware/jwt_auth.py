from functools import wraps
from flask import request ,current_app
from app.utils.response import api_response
import app.services.JWT.Utils

def jwt_required(f):
    """装饰器:保护需要登录的接口，自动验证就问他令牌"""
    @wraps(f)
    def wrapper(*args,**kwargs):
        # 1.从请求头获得令牌
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer"):
            return api_response(401,"未提供令牌，请先登录")

        # 2.提取令牌并使用jwt工具类验证
        token = auth_header.split("")[1]
        payload = JWT_Utils.verify_token(token)
        if not payload:
            return api_response(401,"令牌无效或已过期，请重新登录")
        # 3.录入用户信息值请求对象，供接口使用
        request.user_info = payload
        return f(*args,**kwargs)
    return wrapper