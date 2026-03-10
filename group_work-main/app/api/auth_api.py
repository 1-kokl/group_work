from flask import Blueprint, request
from app.utils.response import api_response
from app.middleware.jwt_auth import jwt_required
from app.services.user_service import user_service  # 你的用户模块
from app.services.JWT_Utils import jwt_service  # 你的JWT服务类

# 定义认证接口蓝图（路径前缀：/api/v1/auth）
auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


# 接口1：用户登录（POST /api/v1/auth/login）
@auth_bp.route("/login", methods=["POST"])
def login():
    # 1. 获取前端提交的登录数据
    data = request.get_json()  # {"username": "test", "password": "Test@123"}
    username = data.get("username")
    password = data.get("password")

    # 2. 调用用户模块校验登录
    user = user_service.login(username, password)
    if not user:
        return api_response(401, user_service.error_msg)  # 如"密码错误，剩余3次"

    # 3. 调用JWT服务类生成令牌
    tokens = jwt_service.generate_tokens(
        username=user.username,
        role=user.role  # 传入角色，用于权限控制
    )
    # 4. 返回令牌（包含access_token和refresh_token）
    return api_response(200, "登录成功", {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"]
    })


# 接口2：刷新访问令牌（POST /api/v1/auth/refresh）
@auth_bp.route("/refresh", methods=["POST"])
def refresh_token():
    # 1. 获取refresh_token
    refresh_token = request.get_json().get("refresh_token")
    if not refresh_token:
        return api_response(400, "缺少refresh_token")

    # 2. 调用JWT服务类验证并生成新access_token
    new_access_token = jwt_service.refresh_access_token(refresh_token)
    if not new_access_token:
        return api_response(401, "refresh_token无效或已过期，请重新登录")

    return api_response(200, "令牌刷新成功", {"access_token": new_access_token})


# 接口3：注销登录（POST /api/v1/auth/logout）
@auth_bp.route("/logout", methods=["POST"])
@jwt_required
def logout():
    # 1. 获取当前令牌并加入黑名单（你的JWT模块需支持）
    current_token = request.headers.get("Authorization").split(" ")[1]
    jwt_service.add_to_blacklist(current_token)

    return api_response(200, "注销成功")