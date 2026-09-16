"""
RBAC + MFA 第一阶段自动化验收测试。

覆盖验收要点：
    1) 角色无越权：普通用户/审计员访问管理接口被拒；商户不能操作他人商品。
    2) 管理员关键操作可追溯：角色变更等写操作落入审计日志。
    3) 恢复流程有边界：TOTP 验证码防重放、恢复码一次性、失步窗口校验。

运行前请先执行 seed_rbac_demo.py 创建演示账号（本脚本会自动调用）。
    PYTHONUTF8=1 python test_rbac.py
"""
import json
import time

import run  # noqa: 构建 app 并注册所有蓝图
from app.extensions import db
from app.services import totp_service
from seed_rbac_demo import seed_demo_accounts

STEP = totp_service.STEP
PASS, FAIL = 0, 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}  {detail}")


def post_json(client, url, data=None, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return client.post(url, json=data or {}, headers=headers)


def put_json(client, url, data=None, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return client.put(url, json=data or {}, headers=headers)


def get_json(client, url, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return client.get(url, headers=headers)


def login_step1(client, username, password):
    """登录第一步，返回响应 JSON。"""
    return post_json(client, "/api/v1/auth/login", {"username": username, "password": password})


def do_totp_bind_confirm_verify(client, username, password, mfa_label):
    """完成 TOTP 绑定 + 确认 + 登录验证，返回 access_token。"""
    # 第一步：密码登录
    r = login_step1(client, username, password)
    check(f"{mfa_label} 登录第一步返回 requires_totp", r.status_code == 200
          and r.get_json()["data"].get("requires_totp") is True)
    mfa_token = r.get_json()["data"]["mfa_token"]

    # 绑定
    r = post_json(client, "/api/v1/auth/totp/bind", {}, token=mfa_token)
    check(f"{mfa_label} TOTP 绑定初始化", r.status_code == 200, r.get_json())
    secret = r.get_json()["data"]["secret"]
    check(f"{mfa_label} 返回 otpauth 扫码串", r.get_json()["data"]["otpauth_uri"].startswith("otpauth://"))

    # 确认（用当前窗口验证码）
    t0 = int(time.time())
    code0 = totp_service.totp_at(secret, t0)
    r = post_json(client, "/api/v1/auth/totp/confirm", {"code": code0}, token=mfa_token)
    check(f"{mfa_label} TOTP 确认绑定", r.status_code == 200, r.get_json())
    recovery_codes = r.get_json()["data"]["recovery_codes"]
    check(f"{mfa_label} 下发 10 个恢复码", len(recovery_codes) == 10)

    # 防重放：复用确认码应被拒
    r = post_json(client, "/api/v1/auth/totp/verify", {"code": code0}, token=mfa_token)
    check(f"{mfa_label} 验证码防重放（复用被拒）", r.status_code == 401, r.get_json())

    # 用下一窗口验证码登录成功
    code1 = totp_service.totp_at(secret, (t0 // STEP + 1) * STEP)
    r = post_json(client, "/api/v1/auth/totp/verify", {"code": code1}, token=mfa_token)
    check(f"{mfa_label} TOTP 二次验证登录成功", r.status_code == 200, r.get_json())
    access_token = r.get_json()["data"]["access_token"]
    return access_token, recovery_codes, secret, mfa_token


def main():
    print("=" * 70)
    print("RBAC + MFA 第一阶段自动化验收测试")
    print("=" * 70)

    seed_demo_accounts()
    app = run.app
    with app.app_context():
        db.create_all()

    # 重置演示账号 TOTP 绑定状态，保证测试可重复执行
    from app.services.user_service import user_service
    user_service.reset_totp("admin")
    user_service.reset_totp("auditor")

    client = app.test_client()

    # ---------- 1. 角色无越权 ----------
    print("\n[1] 角色无越权")

    # 普通用户
    r = login_step1(client, "buyer", "Buyer@123")
    check("普通用户登录（无需 TOTP）", r.status_code == 200 and "access_token" in r.get_json()["data"])
    buyer_token = r.get_json()["data"]["access_token"]
    check("普通用户访问管理员接口 -> 403", get_json(client, "/api/v1/admin/users", buyer_token).status_code == 403)
    check("普通用户创建商品 -> 403", post_json(client, "/api/ecommerce/products",
          {"name": "x", "price": 1}, buyer_token).status_code == 403)
    check("普通用户访问审计日志 -> 403", get_json(client, "/api/v1/audit/logs", buyer_token).status_code == 403)

    # 商户
    r = login_step1(client, "merchant1", "Merchant@123")
    m1_token = r.get_json()["data"]["access_token"]
    r = post_json(client, "/api/ecommerce/products",
                  {"name": "商户1商品", "price": 99, "stock": 10}, m1_token)
    check("商户1 创建商品 -> 201", r.status_code == 201, r.get_json())
    product_id = r.get_json()["data"]["id"]

    r = login_step1(client, "merchant2", "Merchant2@123")
    m2_token = r.get_json()["data"]["access_token"]
    check("商户2 修改商户1商品 -> 403（跨商户越权）",
          put_json(client, f"/api/ecommerce/products/{product_id}",
                   {"price": 1}, m2_token).status_code == 403)
    check("商户2 删除商户1商品 -> 403（跨商户越权）",
          client.delete(f"/api/ecommerce/products/{product_id}",
                        headers={"Authorization": f"Bearer {m2_token}"}).status_code == 403)
    check("商户1 修改自己的商品 -> 200",
          put_json(client, f"/api/ecommerce/products/{product_id}",
                   {"price": 88}, m1_token).status_code == 200)

    # ---------- 2. 管理员 TOTP 双因素 + 关键操作可追溯 ----------
    print("\n[2] 管理员 TOTP 双因素 + 关键操作可追溯")
    admin_token, admin_recovery, admin_secret, admin_mfa = \
        do_totp_bind_confirm_verify(client, "admin", "Admin@123", "管理员")

    # 恢复码一次性
    rc = admin_recovery[0]
    r = post_json(client, "/api/v1/auth/totp/recover", {"recovery_code": rc}, token=admin_mfa)
    check("恢复码登录成功", r.status_code == 200, r.get_json())
    r = post_json(client, "/api/v1/auth/totp/recover", {"recovery_code": rc}, token=admin_mfa)
    check("恢复码二次使用失效（一次性）", r.status_code == 401, r.get_json())

    # 关键操作：角色变更
    r = login_step1(client, "buyer", "Buyer@123")
    buyer_id = None
    with app.app_context():
        from app.services.user_service import user_service
        buyer_id = user_service.get_user_by_username("buyer").id
    r = client.patch(f"/api/v1/admin/users/{buyer_id}/role",
                     json={"role": "merchant"},
                     headers={"Authorization": f"Bearer {admin_token}"})
    check("管理员修改用户角色 -> 200", r.status_code == 200, r.get_json())
    # 改回，避免影响其他测试
    client.patch(f"/api/v1/admin/users/{buyer_id}/role",
                 json={"role": "user"},
                 headers={"Authorization": f"Bearer {admin_token}"})

    # 可追溯：审计日志中应有 USER_ROLE_CHANGE
    r = get_json(client, "/api/v1/audit/logs?action=USER_ROLE_CHANGE", admin_token)
    check("管理员关键操作可追溯（审计日志含 USER_ROLE_CHANGE）",
          r.status_code == 200 and r.get_json()["data"]["total"] >= 1, r.get_json())

    # 越权尝试也被记录
    r = get_json(client, "/api/v1/audit/logs?action=ACCESS_DENIED", admin_token)
    check("越权拒绝被记录（ACCESS_DENIED 日志）",
          r.status_code == 200 and r.get_json()["data"]["total"] >= 1, r.get_json())

    # ---------- 3. 审计员只读 ----------
    print("\n[3] 审计员只读")
    auditor_token, _, _, _ = do_totp_bind_confirm_verify(client, "auditor", "Auditor@123", "审计员")
    check("审计员查看审计日志 -> 200", get_json(client, "/api/v1/audit/logs", auditor_token).status_code == 200)
    check("审计员导出审计日志 -> 200", get_json(client, "/api/v1/audit/logs/export", auditor_token).status_code == 200)
    check("审计员访问用户管理 -> 403（越权）", get_json(client, "/api/v1/admin/users", auditor_token).status_code == 403)
    check("审计员创建商品 -> 403（越权）", post_json(client, "/api/ecommerce/products",
          {"name": "x", "price": 1}, auditor_token).status_code == 403)

    # ---------- 汇总 ----------
    print("\n" + "=" * 70)
    print(f"结果：通过 {PASS} 项，失败 {FAIL} 项")
    print("=" * 70)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
