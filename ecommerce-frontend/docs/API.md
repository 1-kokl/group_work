# API 接口文档（前端视角）

> 后端基于 `group_work-master` 项目。本文件从前端消费角度梳理主要接口、状态码与联调建议。

## 1. 认证模块

| 接口 | 方法 | 描述 | 请求体 | 响应 |
| ---- | ---- | ---- | ------ | ---- |
| `/api/v1/user/login` | POST | 登录 | `{ identifier, password, captcha, captchaKey }` | 成功返回 `{ token, refreshToken, expiresIn, csrfToken, user }`，失败返回 `401/403` |
| `/api/v1/user/register` | POST | 注册并自动登录 | `{ username, email, password, phone, captcha, captchaKey }` | 同登录，附带用户信息 |
| `/api/v1/user/logout` | POST | 注销 | - | `204` 或 `200` |
| `/api/v1/user/token/refresh` | POST | 刷新令牌 | `{ refreshToken }` | 新的 `token/refreshToken/csrfToken` |

### 错误码约定

- `AUTH_INVALID`：用户名或密码错误
- `AUTH_LOCKED`：账号被锁定
- `AUTH_EXPIRED`：令牌过期
- `VALIDATION_FAILED`：字段校验失败

前端在 `src/services/http.js` 中统一映射错误提示，并写入 `window` 事件供全局提示组件使用。

## 2. 用户模块

| 接口 | 方法 | 描述 | 备注 |
| ---- | ---- | ---- | ---- |
| `/api/v1/user/info` | GET | 获取当前用户资料 | 需带 JWT 与 CSRF 头 |
| `/api/v1/users/me` | PATCH | 更新资料（邮箱、简介等） | 支持部分字段更新 |
| `/api/v1/users/me/phone` | PATCH | 更新手机号 | 需后端进行加密与验证 |
| `/api/v1/user/change-password` | POST | 修改密码 | 入参 `{ oldPassword, newPassword }` |
| `/api/v1/user/devices` | GET | 登录设备列表 | 用于安全设置 |

## 3. CAPTCHA、用户名校验（示例）

| 接口 | 方法 | 描述 |
| ---- | ---- | ---- |
| `/api/v1/public/captcha` | GET | 返回 `{ image, key }` |
| `/api/v1/user/check-username` | POST | 校验用户名唯一性 |

## 4. Mock 与测试

- `tests/api/handlers.js`：根据上述接口使用 MSW (Mock Service Worker) 定义 mock 响应。
- `tests/api/login.spec.js`：演示如何验证登录接口的成功/失败分支。
- `npm run serve:mock`：启动开发服务器时启用 MSW 浏览器 worker，可模拟后端响应。

## 5. 调试建议

1. 使用浏览器网络面板检查是否附带了 `Authorization` 与 `X-CSRF-Token`。
2. 若返回 `401`，拦截器会尝试刷新令牌，刷新失败将触发 `auth:token-expired` 事件—需监听并强制登出。
3. `src/services/api/userAPI.js` 内部对关键数据做缓存，可调用 `invalidateUserCaches()` 强制重新拉取。

更多业务接口请参考后端原始 Swagger / Postman 文档，并在此基础上补充字段说明。


