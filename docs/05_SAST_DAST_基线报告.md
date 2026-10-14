# 05 SAST / DAST 与依赖扫描基线报告

> 对应任务书第 7 周节点「SAST/DAST 与依赖扫描」的「基线报告」交付物。
> 复现入口：`run_security_scan.py`；漏洞清单见 `06_漏洞清单.md`。

## 1. 扫描概览

| 项 | 说明 |
| --- | --- |
| 扫描时间 | 2026-10-14 |
| 目标 | 后端（Flask + SQLAlchemy，`app/` + 根目录脚本）、前端（Vue 3） |
| 工具 | SAST: bandit 1.9.4；依赖: pip-audit 2.10.1、npm audit；DAST: 仓库内攻击脚本 + OWASP ZAP（计划） |
| 基线结论 | 静态扫描 13 个 LOW；依赖扫描 4 个组件共 36 个已知漏洞（见 06）；动态测试 3 类防护有效 |

## 2. SAST 基线（bandit）

命令：`python -m bandit -r app -f json -o bandit_report.json`

结果汇总：

| 严重度 | 数量 | 主要问题类型 |
| --- | --- | --- |
| HIGH | 0 | — |
| MEDIUM | 0 | — |
| LOW | 13 | `B105` 硬编码密码、`B311` 非加密随机数、`B404` subprocess、`B112` 异常吞掉 |

LOW 明细（全部）：

| test_id | 位置 | 说明 |
| --- | --- | --- |
| B105 | `app/_init_.py:10` | 硬编码密码字符串 |
| B105 | `app/services/SM3_Service.py:23` | 硬编码密码字符串 |
| B105 | `app/services/user_service.py:52` | 硬编码密码字符串 |
| B105 | `app/utils/jwt_util.py:4` | 硬编码密码字符串 |
| B311 | `app/services/ecommerce_service.py:241` | 使用 `random`（非加密） |
| B311 | `app/services/数据安全层访问.py`（多处） | SM2 签名随机数用 `random`，见 06 |
| B404 | `app/services/数据安全层访问.py:13` | `import subprocess`（潜在命令执行面） |
| B112 | `app/services/SM2_Utils.py:195` | `try/except continue`（可能吞掉错误） |

> bandit 只报 LOW，说明代码没有典型的 `eval`/`pickle`/SQL 字符串拼接等高危静态特征；但人工复核发现若干 bandit 无法识别的**高危设计问题**（私钥入库、非加密随机数用于签名等），详见 `06_漏洞清单.md`。
>
> 注：第 4 周新实现的安全隧道（`app/services/secure_tunnel.py`、`app/middleware/secure_tunnel.py`、`app/api/tunnel_api.py`）未产生任何 bandit 告警。

## 3. 依赖扫描基线（pip-audit）

命令：`python -m pip_audit -r requirements_core.txt --format json`

| 组件 | 当前版本 | 已知漏洞数 | 建议修复版本 |
| --- | --- | --- | --- |
| PyJWT | 2.12.1 | 18 | ≥ 2.13.0（推荐 2.15.0） |
| cryptography | 45.0.6 | 13 | ≥ 46.0.7（部分需 50.0.0） |
| requests | 2.32.3 | 4 | ≥ 2.32.4（推荐 2.33.0） |
| Werkzeug | 3.1.6 | 1 | ≥ 3.1.9 |

> 说明：本项目 JWT 走的是自研 SM2 签名实现（`app/services/JWT_SM2_Utils.py`），并非 PyJWT，因此 PyJWT 的多数 CVE **不直接作用于主认证链路**，但仍属依赖卫生问题，应升级。`cryptography` 被安全隧道（SM4-GCM）与证书签发实际使用，须优先升级。

### 前端依赖（npm audit）

前端 `node_modules` 未在本机安装，`npm audit` 无法现场执行。复现命令：

```bash
cd ecommerce-frontend && npm install && npm audit --json > npm_audit_report.json
```

已知需关注：`axios ^1.7.0`、`element-plus ^2.7.8`、`vue ^3.4.0`（以 `npm audit` 实际结果为准）。

## 4. DAST 基线

| 测试脚本 | 攻击类型 | 结果 |
| --- | --- | --- |
| `test_secure_tunnel.py` | 密文篡改 / 认证标签篡改 / Nonce 重放 / 时间窗过期 / AAD 绑定（8 项断言） | ✅ 全部通过 |
| `test_mitm_attack.py` | 中间人篡改金额 / 伪造签名 | ✅ 签名验证拦截 |
| `test_replay_attack.py` | 100 次重放 + 过期时间戳 | ✅ 防重放拦截 |

实测 `test_secure_tunnel.py` 输出（8 项全 PASS，含 AAD 方法/路径绑定与 Flask 端到端）：

```
[PASS] 正常 SM4-GCM 加密、SM2 封装和解封
[PASS] Nonce 重放
[PASS] 密文篡改
[PASS] 认证标签篡改
[PASS] 时间窗过期
[PASS] AAD 方法/路径绑定
[PASS] Flask /api/v1/tunnel/echo 端到端封装响应
[PASS] Flask 接口拒绝重复 Nonce
```

更完整 DAST 基线（计划）：引入 OWASP ZAP 对 `http://localhost:5000` 做被动+主动扫描，生成 ZAP 报告归档。当前环境未部署 ZAP，先以仓库内脚本化的动态安全测试作为基线。

## 5. 复现方法

```bash
# 一键扫描（自动跳过缺工具项并打印安装命令）
PYTHONUTF8=1 python run_security_scan.py

# 或分步：
python -m bandit -r app -f json -o bandit_report.json              # SAST
python -m pip_audit -r requirements_core.txt --format json          # 依赖
cd ecommerce-frontend && npm audit --json > npm_audit_report.json   # 前端依赖
```

## 6. 结论

- 本次为**首次基线**：静态扫描无 HIGH/MEDIUM 机器告警；依赖层存在 4 个组件 36 个已知 CVE；动态攻击测试 3 类均被现有防护拦截。
- 需要修复的「阻断级」问题及修复计划、责任人，见 `06_漏洞清单.md`。
