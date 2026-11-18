
import json
import time
import urllib.error
import urllib.request

from app.services import totp_service
from seed_rbac_demo import seed_demo_accounts

BASE = "http://localhost:5000"
STEP = totp_service.STEP


class Resp:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body

    def json(self):
        return self._body


def api(method, path, token=None, json_body=None):
    url = BASE + path
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(json_body).encode("utf-8") if json_body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return Resp(resp.status, json.loads(resp.read().decode("utf-8")))
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8"))
        except Exception:
            body = {}
        return Resp(e.code, body)


def sep(title):
    print("\n" + "=" * 66)
    print("  " + title)
    print("=" * 66)


def pause(msg="按回车继续下一步 ..."):
    input("\n  ⏸  " + msg)


def show(resp, fields=()):
    print("    HTTP 状态码:", resp.status_code)
    j = resp.json()
    data = j.get("data") or {}
    for f in fields:
        if f in data:
            val = data[f]
            if isinstance(val, str) and len(val) > 90:
                val = val[:90] + " ..."
            print(f"    {f} = {val}")
    return j


def login(username, password):
    return api("POST", "/api/v1/auth/login", json_body={"username": username, "password": password})


def main():
    seed_demo_accounts()
    # 重置管理员 TOTP 绑定状态
    from app.services.user_service import user_service
    user_service.reset_totp("admin")
    user_service.reset_totp("auditor")

    # ---------- 场景一：角色无越权 ----------
    sep("场景一：角色无越权（普通用户 → 管理接口）")
    print(" 普通用户 buyer 登录，拿 token 访问管理员接口。")
    r = login("buyer", "Buyer@123")
    buyer_token = r.json()["data"]["access_token"]
    print("  buyer 登录成功，拿到 access_token")
    pause()

    r = api("GET", "/api/v1/admin/users", token=buyer_token)
    print("  buyer 访问 GET /api/v1/admin/users：")
    show(r)
    print(" 预期 403 权限不足 —— 被明确拒绝")
    pause()

    r = api("POST", "/api/ecommerce/products", token=buyer_token,
            json_body={"name": "越权商品", "price": 1})
    print("  buyer 尝试创建商品 POST /api/ecommerce/products：")
    show(r)
    print("  预期 403 —— 普通用户不能开店铺")
    pause()

    # ---------- 场景二：跨商户越权 ----------
    sep("场景二：数据级越权（商户二改商户一的商品）")
    print("  商户能创建商品，但只能改自己的商品。")
    m1 = login("merchant1", "Merchant@123").json()["data"]["access_token"]
    m2 = login("merchant2", "Merchant2@123").json()["data"]["access_token"]

    r = api("POST", "/api/ecommerce/products", token=m1,
            json_body={"name": "商户一的演示商品", "price": 99, "stock": 10})
    pid = r.json()["data"]["id"]
    print(f"  merchant1 创建商品成功，商品ID = {pid}")
    pause()

    r = api("PUT", f"/api/ecommerce/products/{pid}", token=m2, json_body={"price": 1})
    print("  merchant2 修改 merchant1 的商品：")
    show(r)
    print("  预期 403 只能操作自己的商品")
    pause()

    # ---------- 场景三：管理员 TOTP 绑定 + 验证 ----------
    sep("场景三：管理员 TOTP 双因素登录")
    print("  管理员登录不是直接放行，而是先要二次验证。")
    r = login("admin", "Admin@123")
    d = r.json()["data"]
    print("  admin 密码登录后返回：")
    print(f"    requires_totp = {d.get('requires_totp')}")
    print(f"    totp_enabled  = {d.get('totp_enabled')}（未绑定）")
    mfa_token = d["mfa_token"]
    pause()

    r = api("POST", "/api/v1/auth/totp/bind", token=mfa_token)
    secret = r.json()["data"]["secret"]
    uri = r.json()["data"]["otpauth_uri"]
    print("  调用 /totp/bind 返回扫码串与密钥：")
    print("    otpauth_uri =", uri)
    print("    请现在用手机认证器扫码（或手动导入 secret）")
    pause("扫码后按回车，脚本会自动算出手机上的验证码")

    code0 = input("    请输入手机上的 6 位验证码（直接回车则自动生成）：").strip()
    if not code0:
        code0 = totp_service.totp_at(secret, int(time.time()))
        print(f"    （自动生成）当前验证码：{code0}")
    r = api("POST", "/api/v1/auth/totp/confirm", token=mfa_token, json_body={"code": code0})
    print("  用第一个验证码 confirm 绑定：")
    show(r, ["recovery_codes"])
    recovery = r.json()["data"]["recovery_codes"]
    print("   绑定成功，一次性下发 10 条恢复码（只显示这一次）")
    pause()

    code1 = input("    请输入手机上的下一个 6 位验证码（直接回车则自动生成）：").strip()
    if not code1:
        code1 = totp_service.totp_at(secret, (int(time.time()) // STEP + 1) * STEP)
        print(f"    （自动生成）下一个验证码：{code1}")
    r = api("POST", "/api/v1/auth/totp/verify", token=mfa_token, json_body={"code": code1})
    print("  用下一个验证码 verify 登录：")
    show(r, ["access_token"])
    admin_token = r.json()["data"]["access_token"]
    print("   二次验证通过，拿到正式 access_token")
    pause()

    # ---------- 场景四：恢复有边界 ----------
    sep("场景四：恢复流程有边界（防重放 + 恢复码一次性）")
    print("  验证码和恢复码都只能各用一次。")
    r = api("POST", "/api/v1/auth/totp/verify", token=mfa_token, json_body={"code": code1})
    print("  复用刚才的验证码 code1：")
    show(r)
    print("  预期 401 验证码已使用（防重放）")
    pause()

    rc = recovery[0]
    r = api("POST", "/api/v1/auth/totp/recover", token=mfa_token, json_body={"recovery_code": rc})
    print(f"  用恢复码 {rc} 登录：")
    show(r, ["access_token"])
    print("   恢复码登录成功")
    pause()

    r = api("POST", "/api/v1/auth/totp/recover", token=mfa_token, json_body={"recovery_code": rc})
    print(f"  再次用同一条恢复码 {rc}：")
    show(r)
    print(" 预期 401 恢复码已使用（一次性）")
    pause()

    # ---------- 场景五：可追溯 ----------
    sep("场景五：管理员关键操作可追溯")
    print("  管理员改角色会写审计日志。")
    from app.services.user_service import user_service
    buyer_id = user_service.get_user_by_username("buyer").id
    r = api("PATCH", f"/api/v1/admin/users/{buyer_id}/role", token=admin_token,
            json_body={"role": "merchant"})
    print("  管理员把 buyer 改为 merchant：")
    show(r)
    api("PATCH", f"/api/v1/admin/users/{buyer_id}/role", token=admin_token,
        json_body={"role": "user"})  # 改回，避免影响
    pause()

    r = api("GET", "/api/v1/audit/logs?action=USER_ROLE_CHANGE", token=admin_token)
    j = show(r)
    total = (j.get("data") or {}).get("total", 0)
    print(f"  审计日志中 USER_ROLE_CHANGE 共 {total} 条")
    print("   可追溯到谁改的、改成什么")
    pause()

    sep("演示结束")
    print("      PYTHONUTF8=1 python test_rbac.py")


if __name__ == "__main__":
    main()
