from flask import Blueprint, request
from app.utils.response import api_response
from app.middleware.jwt_auth import jwt_required
from app.services.SM2_Utils import SM2Service
from app.services.user_service import user_service

# 定义用户接口蓝图（路径前缀：/api/v1）
user_bp = Blueprint("user", __name__, url_prefix="/api/v1")

sm2_service = SM2Service()


# 接口1：用户注册（POST /api/v1/users）
@user_bp.route("/users", methods=["POST"])
def register():
    # 1. 获取前端提交的注册数据
    data = request.get_json()  # 格式：{"username": "test", "password": "Test@123", "phone": "13800138000"}
    username = data.get("username")
    password = data.get("password")
    phone = data.get("phone")

    # 2. 基础参数校验
    if not all([username, password, phone]):
        return api_response(400, "用户名、密码、手机号不能为空")

    # 3. 调用 SM2 加密手机号（替换原来的 RSA）
    try:
        encrypted_phone = sm2_service.encrypt(phone)
    except Exception as e:
        return api_response(500, f"手机号加密失败：{str(e)}")

    # 4. 调用用户模块完成注册
    result = user_service.register(
        username=username,
        password=password,
        phone=phone,
        phone_encrypted=encrypted_phone,
    )
    # 5. 统一响应
    if result["success"]:
        return api_response(201, "注册成功", {"username": username})
    else:
        return api_response(400, result["msg"])


# 接口2：获取当前用户信息（GET /api/v1/users/me）
@user_bp.route("/users/me", methods=["GET"])
@jwt_required
def get_current_user():
    username = request.user_info["username"]
    user = user_service.get_user_by_username(username)
    if not user:
        return api_response(404, "用户不存在")

    return api_response(200, "查询成功", {
        "username": user.username,
        "role": user.role,
        "phone_encrypted": user.phone_encrypted[:5] + "..."
    })


# 接口3：更新用户手机号（PATCH /api/v1/users/me/phone）
@user_bp.route("/users/me/phone", methods=["PATCH"])
@jwt_required
def update_phone():
    new_phone = request.get_json().get("phone")
    username = request.user_info["username"]

    import re
    if not new_phone or not re.match(r'^1[3-9]\d{9}$', new_phone):
        return api_response(400, "手机号格式错误（11位数字）")

    # 加密新手机号（改用 SM2）
    try:
        encrypted_phone = sm2_service.encrypt(new_phone)
    except Exception as e:
        return api_response(500, f"加密失败：{str(e)}")

    success = user_service.update_user_phone(username, encrypted_phone, new_phone)
    if success:
        return api_response(200, "手机号更新成功")
    else:
        return api_response(500, "更新失败，请重试")