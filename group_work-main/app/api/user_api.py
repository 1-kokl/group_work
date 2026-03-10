from flask import Blueprint, request
from app.utils.response import api_response
from app.middleware.jwt_auth import jwt_required
from app.services.rsa_service import rsa_service
from app.services.user_service import user_service

# 定义用户接口蓝图（路径前缀：/api/v1）
user_bp = Blueprint("user", __name__, url_prefix="/api/v1")


# 接口1：用户注册（POST /api/v1/users）
@user_bp.route("/users", methods=["POST"])
def register():
    # 1. 获取前端提交的注册数据
    data = request.get_json()  # 格式：{"username": "test", "password": "Test@123", "phone": "13800138000"}
    username = data.get("username")
    password = data.get("password")
    phone = data.get("phone")

    # 2. 基础参数校验（复用你用户模块的校验逻辑）
    if not all([username, password, phone]):
        return api_response(400, "用户名、密码、手机号不能为空")

    # 3. 调用RSA服务类加密手机号
    try:
        encrypted_phone = rsa_service.encrypt(phone)  
    except Exception as e:
        return api_response(500, f"手机号加密失败：{str(e)}")

    # 4. 调用用户模块完成注册
    result = user_service.register(
        username=username,
        password=password,
        phone_encrypted=encrypted_phone
    )
    # 5. 统一响应（根据注册结果返回）
    if result["success"]:
        return api_response(201, "注册成功", {"username": username})  # 201=创建成功
    else:
        return api_response(400, result["msg"])  # 如"用户名已存在"


# 接口2：获取当前用户信息（GET /api/v1/users/me）
@user_bp.route("/users/me", methods=["GET"])
@jwt_required  # 必须登录才能访问（调用JWT装饰器）
def get_current_user():
    # 1. 从JWT令牌中获取用户名（装饰器已解析并存入request）
    username = request.user_info["username"]

    # 2. 调用用户模块查询信息
    user = user_service.get_user_by_username(username)
    if not user:
        return api_response(404, "用户不存在")

    # 3. 敏感信息脱敏（不返回明文）
    return api_response(200, "查询成功", {
        "username": user.username,
        "role": user.role,
        "phone_encrypted": user.phone_encrypted[:5] + "..."  # 只显示部分加密内容
    })


# 接口3：更新用户手机号（PATCH /api/v1/users/me/phone）
@user_bp.route("/users/me/phone", methods=["PATCH"])
@jwt_required
def update_phone():
    # 1. 获取新手机号和当前用户名
    new_phone = request.get_json().get("phone")
    username = request.user_info["username"]

    # 2. 校验手机号格式
    if not new_phone or not new_phone.match(r'^1[3-9]\d{9}$'):
        return api_response(400, "手机号格式错误（11位数字）")

    # 3. 调用RSA服务类加密新手机号
    try:
        encrypted_phone = rsa_service.encrypt(new_phone)
    except Exception as e:
        return api_response(500, f"加密失败：{str(e)}")

    # 4. 调用用户模块更新信息
    success = user_service.update_user_phone(username, encrypted_phone, new_phone)
    if success:
        return api_response(200, "手机号更新成功")
    else:
        return api_response(500, "更新失败，请重试")