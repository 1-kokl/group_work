from flask import Blueprint, request
from app.utils.response import api_response
from app.middleware.jwt_auth import jwt_required, mfa_token_required
from app.middleware.rbac import ROLE_ADMIN, ROLE_AUDITOR
from app.services.user_service import user_service
from app.services.audit_service import write_log
from app.services.totp_service import (
    verify_totp, generate_secret, build_otpauth_uri,
    generate_recovery_codes, hash_recovery_code,
)
from app.services.JWT_SM2_Utils import jwt_service

# 定义认证接口蓝图（路径前缀：/api/v1/auth）
auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

# 需要启用 TOTP 双因素的角色
_TOTP_ROLES = (ROLE_ADMIN, ROLE_AUDITOR)


def _ip():
    return getattr(request, "remote_addr", None)


def _audit(user_info, action, result="success", resource=None, resource_id=None, detail=""):
    write_log(
        user_id=user_info.get("user_id"),
        username=user_info.get("username"),
        role=user_info.get("role"),
        action=action,
        resource=resource,
        resource_id=resource_id,
        result=result,
        ip=_ip(),
        detail=detail,
    )


def _issue_tokens(username, role, user_id):
    return jwt_service.generate_tokens(username=username, role=role, user_id=user_id)


# 接口1：用户登录（POST /api/v1/auth/login）
# 管理员 / 审计员走两步：第一步密码通过后返回「待二次验证」短时令牌，再走 TOTP。
@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json(silent=True) or {}
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return api_response(400, "用户名和密码不能为空")

        user = user_service.login(username, password)
        if not user:
            write_log(username=username, action="AUTH_LOGIN_FAIL", result="failure",
                      ip=_ip(), detail=user_service.error_msg)
            return api_response(401, user_service.error_msg or "用户名或密码错误")

        role = user.role or "user"

        # 管理员 / 审计员强制 TOTP 双因素
        if role in _TOTP_ROLES:
            mfa_token = jwt_service.generate_token(
                {"username": user.username, "role": role, "user_id": user.id, "mfa": "pending"},
                expires_in=300,
            )
            _audit({"username": user.username, "role": role, "user_id": user.id},
                   "AUTH_LOGIN_TOTP_REQUIRED",
                   detail=f"{role} 需要 TOTP 二次验证")
            return api_response(200, "需要二次验证", {
                "requires_totp": True,
                "totp_enabled": user_service.is_totp_enabled(user.username),
                "mfa_token": mfa_token,
            })

        # 普通用户 / 商户直接签发正式令牌
        tokens = _issue_tokens(user.username, role, user.id)
        _audit({"username": user.username, "role": role, "user_id": user.id}, "AUTH_LOGIN_SUCCESS")
        return api_response(200, "登录成功", {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
        })
    except Exception as e:
        print(f"❌ 登录异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return api_response(500, f"登录失败: {str(e)}")


# 接口2：刷新访问令牌（POST /api/v1/auth/refresh）
@auth_bp.route("/refresh", methods=["POST"])
def refresh_token():
    refresh_token = (request.get_json(silent=True) or {}).get("refresh_token")
    if not refresh_token:
        return api_response(400, "缺少refresh_token")

    new_access_token = jwt_service.refresh_access_token(refresh_token)
    if not new_access_token:
        return api_response(401, "refresh_token无效或已过期，请重新登录")

    return api_response(200, "令牌刷新成功", {"access_token": new_access_token})


# 接口3：注销登录（POST /api/v1/auth/logout）
@auth_bp.route("/logout", methods=["POST"])
@jwt_required
def logout():
    parts = request.headers.get("Authorization", "").split()
    if len(parts) != 2:
        return api_response(401, "令牌格式错误")
    current_token = parts[1]
    jwt_service.add_to_blacklist(current_token)
    _audit(request.user_info, "AUTH_LOGOUT")
    return api_response(200, "注销成功")


# ===================== TOTP 双因素认证接口 =====================
# 以下接口均需「待二次验证」令牌（mfa_token），即第一步密码校验通过后取得。

# 绑定初始化：生成密钥与扫码串
@auth_bp.route("/totp/bind", methods=["POST"])
@mfa_token_required
def totp_bind():
    username = request.user_info["username"]
    role = request.user_info.get("role")
    if user_service.is_totp_enabled(username):
        return api_response(400, "TOTP 已绑定，如需更换请先禁用")

    secret = generate_secret()
    user_service.save_totp_secret(username, secret)
    uri = build_otpauth_uri(username, secret)

    _audit(request.user_info, "TOTP_BIND_INIT", resource="totp", detail="生成密钥与扫码串")
    return api_response(200, "TOTP 绑定初始化成功，请使用认证器扫码", {
        "secret": secret,
        "otpauth_uri": uri,
    })


# 确认绑定：用首个验证码激活，并一次性下发恢复码
@auth_bp.route("/totp/confirm", methods=["POST"])
@mfa_token_required
def totp_confirm():
    username = request.user_info["username"]
    code = (request.get_json(silent=True) or {}).get("code")

    secret = user_service.get_totp_secret(username)
    if not secret:
        return api_response(400, "尚未初始化绑定，请先调用 /totp/bind")

    ok, counter = verify_totp(secret, code)
    if not ok:
        _audit(request.user_info, "TOTP_VERIFY_FAIL", result="failure", resource="totp",
               detail="绑定确认验证码错误")
        return api_response(400, "验证码错误")

    recovery_codes = generate_recovery_codes()
    recovery_hashes = [hash_recovery_code(c) for c in recovery_codes]
    user_service.enable_totp(username, recovery_hashes, counter)

    _audit(request.user_info, "TOTP_BIND_CONFIRM", resource="totp", detail="TOTP 已启用")
    return api_response(200, "TOTP 绑定成功，请妥善保存恢复码（仅此一次展示）", {
        "recovery_codes": recovery_codes,
    })


# 第二步验证：校验 TOTP 验证码（含防重放）
@auth_bp.route("/totp/verify", methods=["POST"])
@mfa_token_required
def totp_verify():
    username = request.user_info["username"]
    role = request.user_info.get("role")
    user_id = request.user_info.get("user_id")
    code = (request.get_json(silent=True) or {}).get("code")

    secret = user_service.get_totp_secret(username)
    if not secret:
        return api_response(400, "尚未绑定 TOTP")

    ok, counter = verify_totp(secret, code)
    if not ok:
        _audit(request.user_info, "TOTP_VERIFY_FAIL", result="failure", resource="totp",
               detail="动态验证码错误")
        return api_response(401, "动态验证码错误")

    # 防重放：计数器必须严格递增，同一窗口验证码不可复用
    last_counter = user_service.get_last_totp_counter(username)
    if counter <= last_counter:
        _audit(request.user_info, "TOTP_REPLAY_BLOCKED", result="denied", resource="totp",
               detail="验证码已使用（重放）")
        return api_response(401, "验证码已使用，请等待下一个验证码")

    user_service.set_last_totp_counter(username, counter)
    tokens = _issue_tokens(username, role, user_id)

    _audit(request.user_info, "TOTP_VERIFY_SUCCESS", resource="totp")
    _audit(request.user_info, "AUTH_LOGIN_SUCCESS", detail="TOTP 双因素登录成功")
    return api_response(200, "二次验证通过，登录成功", {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
    })


# 恢复码登录：设备丢失 / 无法生成验证码时的兜底通道
@auth_bp.route("/totp/recover", methods=["POST"])
@mfa_token_required
def totp_recover():
    username = request.user_info["username"]
    role = request.user_info.get("role")
    user_id = request.user_info.get("user_id")
    recovery_code = (request.get_json(silent=True) or {}).get("recovery_code")

    if not recovery_code:
        return api_response(400, "请提供恢复码")

    code_hash = hash_recovery_code(recovery_code)
    if not user_service.consume_recovery_code(username, code_hash):
        _audit(request.user_info, "TOTP_RECOVER_FAIL", result="failure", resource="totp",
               detail="恢复码无效或已使用")
        return api_response(401, "恢复码无效或已使用")

    tokens = _issue_tokens(username, role, user_id)
    _audit(request.user_info, "TOTP_RECOVER", resource="totp", detail="使用恢复码登录")
    return api_response(200, "恢复成功，登录成功", {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
    })


# 禁用 TOTP：需提供有效动态验证码或恢复码
@auth_bp.route("/totp/disable", methods=["POST"])
@mfa_token_required
def totp_disable():
    username = request.user_info["username"]
    data = request.get_json(silent=True) or {}
    code = data.get("code")
    recovery_code = data.get("recovery_code")

    secret = user_service.get_totp_secret(username)
    authorized = False

    if code and secret:
        ok, _ = verify_totp(secret, code)
        if ok:
            last_counter = user_service.get_last_totp_counter(username)
            ok, counter = verify_totp(secret, code)
            authorized = ok and counter > last_counter
    if not authorized and recovery_code:
        authorized = user_service.consume_recovery_code(username, hash_recovery_code(recovery_code))

    if not authorized:
        _audit(request.user_info, "TOTP_DISABLE_FAIL", result="denied", resource="totp",
               detail="缺少有效验证码或恢复码")
        return api_response(403, "禁用 TOTP 需提供有效动态验证码或恢复码")

    user_service.disable_totp(username)
    _audit(request.user_info, "TOTP_DISABLE", resource="totp", detail="TOTP 已禁用")
    return api_response(200, "TOTP 已禁用")


# 查询 TOTP 绑定状态
@auth_bp.route("/totp/status", methods=["GET"])
@mfa_token_required
def totp_status():
    username = request.user_info["username"]
    enabled = user_service.is_totp_enabled(username)
    remaining = len(user_service.get_recovery_hashes(username)) if enabled else 0
    return api_response(200, "查询成功", {
        "totp_enabled": enabled,
        "recovery_codes_remaining": remaining,
    })
