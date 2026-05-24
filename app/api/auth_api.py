from flask import Blueprint, request
from app.utils.response import api_response
from app.middleware.jwt_auth import jwt_required
from app.services.user_service import user_service
from app.services.JWT_SM2_Utils import jwt_service

# 定义认证接口蓝图（路径前缀：/api/v1/auth）
auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


# 接口1：用户登录（POST /api/v1/auth/login）
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = user_service.login(username, password)
    if not user:
        return api_response(401, user_service.error_msg, None)

    tokens = jwt_service.generate_tokens(
        username=user.username,
        role=user.role,
        user_id=user.id
    )
    return api_response(200, "登录成功", {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"]
    })


# 接口2：刷新访问令牌（POST /api/v1/auth/refresh）
@auth_bp.route("/refresh", methods=["POST"])
def refresh_token():
    refresh_token = request.get_json().get("refresh_token")
    if not refresh_token:
        return api_response(400, "缺少refresh_token", None)

    new_access_token = jwt_service.refresh_access_token(refresh_token)
    if not new_access_token:
        return api_response(401, "refresh_token无效或已过期，请重新登录", None)

    return api_response(200, "令牌刷新成功", {"access_token": new_access_token})


# 接口3：注销登录（POST /api/v1/auth/logout）
@auth_bp.route("/logout", methods=["POST"])
@jwt_required
def logout():
    parts = request.headers.get("Authorization", "").split()
    if len(parts) != 2:
        return api_response(401, "令牌格式错误", None)
    current_token = parts[1]
    jwt_service.add_to_blacklist(current_token)

    return api_response(200, "注销成功", None)
