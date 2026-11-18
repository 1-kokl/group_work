"""
RBAC 访问控制中间件。

模型：用户(User) → 角色(Role) → 权限(Permission)。

- ROLES：系统 4 个角色（管理员 admin / 商户 merchant / 普通用户 user / 审计员 auditor）。
- PERMISSION_MATRIX：权限矩阵，key 为「资源.操作」，value 为允许执行该操作的角色集合。
- require_permission / require_role：视图装饰器，越权时返回 403 并写入 ACCESS_DENIED 审计日志。

数据级权限（如「商户只能改自己的商品」）不在矩阵内表达，而在对应路由/服务中
按资源归属二次校验（见 ecommerce_routes.py 的商品归属判断），这是「最小权限」的体现。

注意：装饰器需置于 @jwt_required 之上（外层），保证先通过认证再检查授权。
"""
from functools import wraps

from flask import request

from app.services.audit_service import write_log
from app.utils.response import api_response

# 角色常量
ROLE_USER = "user"        # 普通用户（买家）
ROLE_MERCHANT = "merchant"  # 商户（卖家）
ROLE_ADMIN = "admin"      # 管理员
ROLE_AUDITOR = "auditor"  # 审计员（只读）

ALL_ROLES = (ROLE_USER, ROLE_MERCHANT, ROLE_ADMIN, ROLE_AUDITOR)

# 权限矩阵：资源.操作 -> 允许角色集合
PERMISSION_MATRIX = {
    # ---- 商品 ----
    "product.view":     {ROLE_USER, ROLE_MERCHANT, ROLE_ADMIN, ROLE_AUDITOR},  # 公开浏览
    "product.create":   {ROLE_ADMIN, ROLE_MERCHANT},
    "product.update":   {ROLE_ADMIN, ROLE_MERCHANT},  # 商户仅限自有商品（路由内二次校验）
    "product.delete":   {ROLE_ADMIN, ROLE_MERCHANT},  # 商户仅限自有商品（路由内二次校验）

    # ---- 购物车 / 订单（天然按 owner 自限）----
    "cart.manage":      {ROLE_USER, ROLE_MERCHANT},
    "order.create":     {ROLE_USER, ROLE_MERCHANT},
    "order.view_own":   {ROLE_USER, ROLE_MERCHANT},
    "order.cancel_own": {ROLE_USER, ROLE_MERCHANT},
    "order.pay_own":    {ROLE_USER, ROLE_MERCHANT},
    "order.view_any":   {ROLE_ADMIN},

    # ---- 用户 / 自身资料 ----
    "user.profile_self": {ROLE_USER, ROLE_MERCHANT, ROLE_ADMIN, ROLE_AUDITOR},

    # ---- 用户管理（仅管理员）----
    "user.create":        {ROLE_ADMIN},
    "user.list":          {ROLE_ADMIN},
    "user.role_change":   {ROLE_ADMIN},
    "user.status_change": {ROLE_ADMIN},
    "user.password_reset": {ROLE_ADMIN},

    # ---- 审计（审计员只读 + 管理员）----
    "audit.view":            {ROLE_AUDITOR, ROLE_ADMIN},
    "audit.export":          {ROLE_AUDITOR, ROLE_ADMIN},
    "audit.security_events": {ROLE_AUDITOR, ROLE_ADMIN},

    # ---- TOTP 双因素（管理员/审计员自绑定；管理员可代重置）----
    "totp.bind":      {ROLE_ADMIN, ROLE_AUDITOR},
    "totp.verify":    {ROLE_ADMIN, ROLE_AUDITOR},
    "totp.recover":   {ROLE_ADMIN, ROLE_AUDITOR},
    "totp.disable":   {ROLE_ADMIN, ROLE_AUDITOR},
    "totp.status":    {ROLE_ADMIN, ROLE_AUDITOR},
    "totp.reset_any": {ROLE_ADMIN},
}


def _current_role():
    return (request.user_info or {}).get("role", ROLE_USER)


def _deny(permission, reason=None):
    """越权：写审计日志并返回 403。"""
    info = request.user_info or {}
    write_log(
        user_id=info.get("user_id"),
        username=info.get("username"),
        role=info.get("role"),
        action="ACCESS_DENIED",
        resource=permission,
        result="denied",
        ip=getattr(request, "remote_addr", None),
        detail=reason or f"缺少权限: {permission}",
    )
    return api_response(403, "权限不足，拒绝访问")


def require_permission(permission):
    """要求当前用户角色拥有指定权限。"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            role = _current_role()
            allowed = PERMISSION_MATRIX.get(permission, set())
            if role not in allowed:
                return _deny(permission)
            return f(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(*permissions):
    """要求当前用户角色拥有任意一个权限（等价于 OR）。"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            role = _current_role()
            if not any(role in PERMISSION_MATRIX.get(p, set()) for p in permissions):
                return _deny("/".join(permissions))
            return f(*args, **kwargs)
        return wrapper
    return decorator


def require_role(*roles):
    """直接按角色放行（角色粒度，无需细化到权限时使用）。"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            role = _current_role()
            if role not in roles:
                return _deny(f"role:{role}", reason=f"需要角色: {'/'.join(roles)}")
            return f(*args, **kwargs)
        return wrapper
    return decorator
