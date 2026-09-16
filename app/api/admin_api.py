"""管理员 / 审计员接口。

- /api/v1/admin/*   ：用户管理（仅管理员，含 TOTP 代重置的恢复边界）
- /api/v1/audit/*   ：审计日志查询/导出（审计员只读 + 管理员）

所有写操作均写审计日志，支撑「管理员关键操作可追溯」。
"""
from flask import Blueprint, request

from app.middleware.jwt_auth import jwt_required
from app.middleware.rbac import require_permission
from app.services.user_service import user_service, VALID_ROLES
from app.services.audit_service import write_log, query_logs, count_logs
from app.utils.response import api_response

admin_bp = Blueprint("admin", __name__, url_prefix="/api/v1")


def _audit(user_info, action, result="success", resource=None, resource_id=None, detail=""):
    write_log(
        user_id=user_info.get("user_id"),
        username=user_info.get("username"),
        role=user_info.get("role"),
        action=action,
        resource=resource,
        resource_id=resource_id,
        result=result,
        ip=getattr(request, "remote_addr", None),
        detail=detail,
    )


# ===================== 用户管理（管理员） =====================

@admin_bp.route("/admin/users", methods=["GET"])
@jwt_required
@require_permission("user.list")
def admin_list_users():
    role = request.args.get("role")
    users = user_service.list_users(role=role)
    _audit(request.user_info, "USER_MANAGE_LIST", resource="user",
           detail=f"查询用户列表 role={role or 'all'}")
    return api_response(200, "查询成功", {"users": users})


@admin_bp.route("/admin/users", methods=["POST"])
@jwt_required
@require_permission("user.create")
def admin_create_user():
    """管理员创建指定角色的用户（现场演示：新建账号再登录）。"""
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "user")

    if not username or not password:
        return api_response(400, "用户名和密码不能为空")
    if role not in VALID_ROLES:
        return api_response(400, f"非法角色，允许值: {', '.join(VALID_ROLES)}")
    if user_service.get_user_by_username(username):
        return api_response(400, "用户名已存在")

    result = user_service.register(username, password, phone="", phone_encrypted="")
    if not result["success"]:
        return api_response(400, result["msg"])

    u = user_service.get_user_by_username(username)
    user_service.change_role(u.id, role)

    _audit(request.user_info, "USER_CREATE", resource="user", resource_id=str(u.id),
           detail=f"创建用户 {username}，角色 {role}")
    return api_response(201, "用户创建成功", {"username": username, "role": role})


@admin_bp.route("/admin/users/<int:user_id>/role", methods=["PATCH"])
@jwt_required
@require_permission("user.role_change")
def admin_change_role(user_id):
    new_role = (request.get_json(silent=True) or {}).get("role")
    if not new_role:
        return api_response(400, "缺少 role 参数")

    # 防止管理员把自己降权导致锁死系统
    if request.user_info.get("user_id") == user_id:
        return api_response(400, "不能修改自己的角色")

    target = user_service.get_user_by_id(user_id)
    if not target:
        return api_response(404, "用户不存在")

    old_role = target.role
    ok, err = user_service.change_role(user_id, new_role)
    if not ok:
        return api_response(400, err)

    _audit(request.user_info, "USER_ROLE_CHANGE", resource="user", resource_id=str(user_id),
           detail=f"{target.username}: {old_role} -> {new_role}")
    return api_response(200, "角色修改成功", {"user_id": user_id, "role": new_role})


@admin_bp.route("/admin/users/<int:user_id>/status", methods=["PATCH"])
@jwt_required
@require_permission("user.status_change")
def admin_change_status(user_id):
    status = (request.get_json(silent=True) or {}).get("status")  # true=启用 false=禁用
    target = user_service.get_user_by_id(user_id)
    if not target:
        return api_response(404, "用户不存在")

    if request.user_info.get("user_id") == user_id:
        return api_response(400, "不能修改自己的状态")

    user_service.set_user_status(user_id, status)
    _audit(request.user_info, "USER_STATUS_CHANGE", resource="user", resource_id=str(user_id),
           detail=f"{target.username}: {'启用' if status else '禁用'}")
    return api_response(200, "状态修改成功", {"user_id": user_id, "status": bool(status)})


@admin_bp.route("/admin/users/<int:user_id>/reset-password", methods=["POST"])
@jwt_required
@require_permission("user.password_reset")
def admin_reset_password(user_id):
    new_password = (request.get_json(silent=True) or {}).get("password")
    if not new_password or len(new_password) < 8:
        return api_response(400, "新密码至少 8 位")

    target = user_service.get_user_by_id(user_id)
    if not target:
        return api_response(404, "用户不存在")

    user_service.reset_password(user_id, new_password)
    _audit(request.user_info, "USER_PASSWORD_RESET", resource="user", resource_id=str(user_id),
           detail=f"重置 {target.username} 的密码")
    return api_response(200, "密码重置成功")


@admin_bp.route("/admin/users/<int:user_id>/totp/reset", methods=["POST"])
@jwt_required
@require_permission("totp.reset_any")
def admin_reset_totp(user_id):
    """恢复边界：设备丢失且恢复码耗尽时，仅管理员可代为重置 TOTP。"""
    target = user_service.get_user_by_id(user_id)
    if not target:
        return api_response(404, "用户不存在")

    user_service.reset_totp(target.username)
    _audit(request.user_info, "TOTP_RESET_BY_ADMIN", resource="totp", resource_id=str(user_id),
           detail=f"管理员重置 {target.username} 的 TOTP 绑定")
    return api_response(200, "TOTP 绑定已重置，用户需重新绑定")


# ===================== 审计日志（审计员 / 管理员） =====================

@admin_bp.route("/audit/logs", methods=["GET"])
@jwt_required
@require_permission("audit.view")
def audit_view():
    action = request.args.get("action")
    username = request.args.get("username")
    result = request.args.get("result")
    limit = request.args.get("limit", 100, type=int)
    offset = request.args.get("offset", 0, type=int)

    logs = query_logs(action=action, username=username, result=result, limit=limit, offset=offset)
    total = count_logs(action=action, username=username, result=result)
    _audit(request.user_info, "AUDIT_VIEW", resource="audit",
           detail=f"查看审计日志 action={action or 'all'} result={result or 'all'}")
    return api_response(200, "查询成功", {"total": total, "items": logs})


@admin_bp.route("/audit/logs/export", methods=["GET"])
@jwt_required
@require_permission("audit.export")
def audit_export():
    limit = request.args.get("limit", 1000, type=int)
    logs = query_logs(limit=limit)
    _audit(request.user_info, "AUDIT_EXPORT", resource="audit",
           detail=f"导出审计日志 {len(logs)} 条")
    # 简化导出：返回 JSON 数组（可扩展为 CSV/文件）
    return api_response(200, "导出成功", {"count": len(logs), "logs": logs})


@admin_bp.route("/audit/security-events", methods=["GET"])
@jwt_required
@require_permission("audit.security_events")
def audit_security_events():
    """安全事件查询：越权拒绝、登录失败、TOTP 失败/重放等异常事件。"""
    interesting = ["ACCESS_DENIED", "AUTH_LOGIN_FAIL", "TOTP_VERIFY_FAIL",
                   "TOTP_REPLAY_BLOCKED", "TOTP_RECOVER_FAIL"]
    events = []
    for act in interesting:
        events.extend(query_logs(action=act, limit=50))
    events.sort(key=lambda e: e["id"], reverse=True)
    _audit(request.user_info, "AUDIT_SECURITY_EVENTS", resource="audit",
           detail="查询安全事件")
    return api_response(200, "查询成功", {"count": len(events), "events": events})
