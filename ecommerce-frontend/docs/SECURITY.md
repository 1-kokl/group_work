## 前端安全指南

### 1. 通信安全

- **HTTPS 强制使用**：生产环境必须通过 HTTPS 部署，防止中间人攻击。
- **CSRF 防护**：`src/services/http.js` 自动附带 `X-CSRF-Token`，后端需校验；接口需启用 SameSite Cookie 策略。
- **JWT 存储**：只在 `localStorage` 保存访问令牌、刷新令牌与过期时间；若使用第三方登录请改为 httpOnly Cookie。

### 2. XSS 防御

- 所有用户输入均使用 `sanitizeInput` / `escapeHTML` 处理。
- 避免使用 `v-html`，若必须使用，先在前端或服务端做白名单过滤。
- CSP 建议配置 `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'`.

### 3. 输入校验

- 统一在 `security.js` 提供的校验器中维护规则；前端只做初筛，后端需再次校验。
- 提示信息不要泄露过多细节，例如“用户名或密码错误”而非具体字段错误。

### 4. 敏感数据处理

- 不在前端缓存用户隐私字段（身份证、银行卡等）；必要时只存脱敏后的信息。
- 表单草稿使用 `localStorage`（已在个人资料页面实现自动清空），提交后立即清理。
- 前端日志中避免输出 token / refreshToken，可使用 `console.debug` 并在生产禁用。

### 5. 依赖安全

- 每月运行 `npm audit` 与 `npm outdated`，及时升级 Element Plus / Vue / Axios。
- 在 CI 中加入 `npm audit --production` 或使用 Snyk/Dependabot 自动告警。

### 6. 常见漏洞检查列表

| 漏洞类型 | 解决方案 |
| -------- | -------- |
| XSS | 输入转义、CSP、避免 `v-html` |
| CSRF | CSRF Token + SameSite Cookie + Referer 检查 |
| Clickjacking | 配置 `X-Frame-Options: DENY` 或 CSP 中的 `frame-ancestors` |
| CORS | 仅开放白名单域名，禁止 `*` |
| SSRF | 与后端协作限制开放接口 |

如发现安全问题，请通过内部安全流程或私信维护者，避免在公开渠道披露。

