# 02 TOTP 双因素认证流程图

> 对应任务书第 2 周节点「RBAC 与 MFA 设计」中的「TOTP 流程图」交付物。
> 实现代码：`app/services/totp_service.py`（RFC 6238 TOTP / RFC 4226 HOTP）、
> `app/api/auth_api.py`（绑定/验证/恢复/禁用接口）。

## 1. 认证总体流程

```mermaid
flowchart TD
    A[用户输入 用户名/密码] --> B[/api/v1/auth/login/]
    B --> C{密码校验}
    C -- 失败 --> D[401 记录 AUTH_LOGIN_FAIL]
    C -- 成功 --> E{角色是否为 admin / auditor?}
    E -- 否（user/merchant） --> F[直接签发 access + refresh token]
    E -- 是 --> G[签发 mfa_token（5min 短时令牌）<br/>返回 requires_totp=true]
    G --> H[第二步：TOTP 验证码 / 恢复码]
    H --> I{验证通过?}
    I -- 否 --> J[401 拒绝]
    I -- 是 --> F
```

> 管理员 / 审计员强制双因素（`auth_api.py:_TOTP_ROLES`），普通用户/商户单因素即可 —— 这是「按角色分级的 MFA 策略」。

## 2. TOTP 绑定流程（首次启用）

```mermaid
sequenceDiagram
    participant U as 用户(admin/auditor)
    participant A as auth_api
    participant T as totp_service
    participant DB as user.db

    U->>A: POST /totp/bind (带 mfa_token)
    A->>T: generate_secret() → Base32 密钥
    A->>DB: save_totp_secret(username, secret)（未启用）
    A->>T: build_otpauth_uri(username, secret)
    A-->>U: 返回 secret + otpauth:// 扫码串
    U->>U: 手机认证器扫码
    U->>A: POST /totp/confirm (code=首个验证码)
    A->>T: verify_totp(secret, code) → (ok, counter)
    alt ok
        A->>T: generate_recovery_codes() → 10 条恢复码
        A->>DB: enable_totp(恢复码哈希, counter)  # 启用
        A-->>U: 返回恢复码（仅此一次展示）
    else 失败
        A-->>U: 400 验证码错误
    end
```

## 3. TOTP 验证（登录第二步，含防重放）

```mermaid
flowchart TD
    A[POST /totp/verify code] --> B[verify_totp secret,code<br/>±1 时间步容错]
    B --> C{命中?}
    C -- 否 --> D[401 记录 TOTP_VERIFY_FAIL]
    C -- 是 --> E[取出命中 counter]
    E --> F{counter > last_counter?}
    F -- 否 --> G[401 记录 TOTP_REPLAY_BLOCKED<br/>同一窗口验证码不可复用]
    F -- 是 --> H[set_last_totp_counter= counter]
    H --> I[签发 access + refresh token]
```

## 4. 恢复码兜底（设备丢失）

```mermaid
flowchart TD
    A[POST /totp/recover<br/>recovery_code] --> B[hash_recovery_code code]
    B --> C{consume_recovery_code?}
    C -- 命中且未使用 --> D[移除该恢复码 → 一次性]
    D --> E[签发 token 记录 TOTP_RECOVER]
    C -- 已用/无效 --> F[401 记录 TOTP_RECOVER_FAIL]
    E2[恢复码耗尽且设备丢失] --> G[仅管理员 POST /admin/users/:id/totp/reset]
    G --> H[reset_totp 兜底<br/>记录 TOTP_RESET_BY_ADMIN]
```

## 5. 算法参数（RFC 6238，与认证器兼容）

| 参数 | 值 |
| --- | --- |
| 哈希算法 | HMAC-SHA1 |
| 时间步长 `STEP` | 30 秒 |
| 码位数 `DIGITS` | 6 |
| 容错窗口 `WINDOW` | ±1 步（容忍 60s 时间偏差） |
| 恢复码数量 | 10 条（`AB12-CD34` 格式，只存 SHA-256 哈希） |

## 6. 验收要点对照

| 验收要点 | 落地 |
| --- | --- |
| 恢复流程有边界 | 验证码防重放（counter 严格递增）＋恢复码一次性（消费即删除）＋管理员代重置兜底 |
| 管理员关键操作可追溯 | 绑定/验证/恢复/禁用/重置均写审计日志（`TOTP_*` 事件） |
| 与实现一致 | `test_rbac.py` 的 `do_totp_bind_confirm_verify` 逐条断言绑定/防重放/登录成功 |
