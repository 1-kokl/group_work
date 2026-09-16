"""
演示账号种子脚本（RBAC + MFA 第一阶段）。

创建 5 个演示账号，覆盖 4 种角色 + 1 个第二商户（用于越权测试）。
幂等：已存在的账号会跳过，不会覆盖。

    python seed_rbac_demo.py

演示账号（详见 docs/06_演示账号.md）：
    admin     / Admin@123     管理员
    auditor   / Auditor@123   审计员
    merchant1 / Merchant@123  商户一
    merchant2 / Merchant2@123 商户二（用于越权测试）
    buyer     / Buyer@123     普通用户
"""
from app.services.user_service import user_service, VALID_ROLES

DEMO_ACCOUNTS = [
    {"username": "admin",     "password": "Admin@123",   "role": "admin"},
    {"username": "auditor",   "password": "Auditor@123", "role": "auditor"},
    {"username": "merchant1", "password": "Merchant@123", "role": "merchant"},
    {"username": "merchant2", "password": "Merchant2@123", "role": "merchant"},
    {"username": "buyer",     "password": "Buyer@123",   "role": "user"},
]


def seed_demo_accounts():
    created, skipped = [], []
    for acc in DEMO_ACCOUNTS:
        existing = user_service.get_user_by_username(acc["username"])
        if existing:
            # 已存在：确保角色正确（便于复跑）
            if existing.role != acc["role"]:
                user_service.change_role(existing.id, acc["role"])
            skipped.append(acc["username"])
            continue
        r = user_service.register(
            username=acc["username"],
            password=acc["password"],
            phone="13800138000",
            phone_encrypted="demo",
        )
        if not r["success"]:
            print(f"  注册失败 {acc['username']}: {r['msg']}")
            continue
        u = user_service.get_user_by_username(acc["username"])
        user_service.change_role(u.id, acc["role"])
        created.append(acc["username"])
    print("演示账号就绪：新建", created, "| 已存在", skipped)


if __name__ == "__main__":
    seed_demo_accounts()
    print()
    print("可用账号（角色）：")
    for acc in DEMO_ACCOUNTS:
        print(f"  {acc['username']:<12} / {acc['password']:<14}  {acc['role']}")
