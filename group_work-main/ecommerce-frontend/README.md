# ecommerce-frontend

面向 `group_work-main`（Flask + SQLite + JWT）的电商运营后台前端项目。基于 **Vue 3 + Element Plus + Vuex**，已针对最新后端联调做了以下改动：

- 登录 / 注册请求体与 `group_work-main/flask_new.py` 一致（用户名 6-20 位、密码必须包含大小写+数字+`!@#$%^&*()`）。
- 成功登录后跳转至静态系统导航页，侧边栏常驻展示登录状态、个人中心、退出登录。
- 会话信息统一存放在 `sessionStorage`，浏览器关闭即自动退出，解决“二次打开白屏”问题。

---

## 快速开始

### 1. 目录结构

```text
zonshe/
├─ ecommerce-frontend/     # 当前项目（Vue 前端）
└─ group_work-main/        # Flask 后端，入口为 flask_new.py / run.py
```

保持两个仓库各自独立，前端通过 `VUE_APP_API_BASE_URL` 指向后端即可联调，无需物理合并。

### 2. 环境要求

- Node.js ≥ 16（推荐 [nvm-windows](https://github.com/coreybutler/nvm-windows)）
- npm ≥ 8
- 后端建议使用 Python 3.9+，依赖 `flask`, `flask-cors`, `flask-jwt-extended`, `sqlalchemy`, `pycryptodome`
- 后端默认监听 `http://127.0.0.1:5000`

### 3. 后端启动（先启动）

```bash
cd ../group_work-main/group_work-main
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt   # 或按 README 安装所需依赖
python flask_new.py               # 或 python run.py
```

首次运行会在目录下生成 `ecommerce.db`、RSA 密钥以及限流所需的 Redis 连接（可选，如未安装 Redis 会自动降级为内存限流）。

### 4. 前端启动

```bash
cd ecommerce-frontend
cp config/environment.example .env.local   # 若已有则直接编辑
# .env.local 中至少配置：
# VUE_APP_API_BASE_URL=http://127.0.0.1:5000

npm install
npm run serve
```

默认开发端口 `8080`，会将 `/api` 请求代理到 `.env` 指定的后端地址。若需本地 MSW Mock，可运行 `npm run serve:mock`。

---

## 登录 / 注册流程

1. 打开 `http://localhost:8080`，先注册新账号：
   - 用户名：字母 / 数字 / 下划线，长度 6-20
   - 密码：≥8 位，且包含大写、小写、数字、特殊符号 `!@#$%^&*()` 中至少一个
   - 手机号：`13/14/15/16/17/18/19` 开头的 11 位
2. 注册成功后前端会自动登录并跳转至 "系统导航" 静态页，左侧栏展示当前账号。
3. 个人中心展示 `sessionStorage` 中的用户名、邮箱、手机号，可在注销按钮直接退出。
4. 浏览器关闭或刷新时会触发 `beforeunload`，后端凭证立即清空，防止 "假登录" 状态。

---

## 目录结构（前端）

```text
src/
├── App.vue               # 根组件，负责布局与路由占位
├── main.js               # 启动入口、MSW 钩子、beforeunload 逻辑
├── router/               # 路由配置（Login、Register、Navigation、Profile 等）
├── store/
│   ├── modules/auth.js   # Token / 用户态管理（使用 sessionStorage）
│   └── modules/user.js   # 个人资料缓存，同步 sessionStorage + localStorage
├── services/
│   ├── http.js           # Axios 实例、401 刷新/降级处理
│   └── api/              # authAPI、userAPI，封装后端契约
├── pages/
│   ├── auth/             # Login / Register（已移除验证码、用户名远程校验）
│   ├── navigation/       # SystemNavigation 静态导航页
│   └── user/             # Profile 静态个人中心（展示缓存信息）
├── components/
│   └── layout/           # AppSidebar 等布局组件（头部已移除）
└── utils/
    ├── security.js       # 输入清洗、密码/用户名/手机号校验，匹配新后端规则
    ├── cache.js          # 前端缓存工具
    └── perf.js           # 防抖/节流等性能函数
```

`docs/` 目录提供 API、组件、部署、安全指南，可结合后端仓库文档一起阅读。

---

## 常用脚本

| 命令                   | 用途                                               |
| ---------------------- | -------------------------------------------------- |
| `npm run serve`        | 开发模式（代理真实后端）                           |
| `npm run serve:mock`   | 开发模式 + MSW Mock                                |
| `npm run build`        | 生成生产包（splitChunks + Brotli + 版本号注入）   |
| `npm run lint`         | ESLint                                             |
| `npm run test:unit`    | 单元测试（Jest + Vue Test Utils）                  |
| `npm run test:api`     | API 契约测试（Jest + MSW Node）                    |
| `npm run test:e2e`     | Cypress 无头端到端测试                             |
| `npm run test:coverage`| 输出覆盖率报告至 `coverage/`                      |

---

## 部署提示

1. 推荐在生产环境中将静态包部署到 Nginx/OSS/CDN，后端单独部署（Gunicorn / uWSGI / Docker）。
2. 使用 `.env.production` 配置正式后端地址（例如云服务器或 HTTPS 域名）。
3. 确保后端响应头已携带 CORS、CSP、HSTS 等安全头；前端仅存储必须的 Token 信息，关闭长时间的本地持久化。

---

## FAQ

| 问题                             | 处理方式                                                         |
| -------------------------------- | ---------------------------------------------------------------- |
| 注册/登录返回 400                | 后端密码/用户名/手机号格式不符，请检查输入是否满足最新规则       |
| 登录后刷新浏览器看到空白页      | 符合设计：关闭/刷新会触发强制退出，请重新登录                    |
| 登录失败提示网络错误            | 401 错误会提示“用户名或密码错误”，其它状态展示后端返回的消息     |
| 需要查看后端 API                 | 打开 `group_work-main/group_work-main/README.md` 或 `api文档.md` |
| 想体验移动端                    | 当前布局仅针对桌面端，可在 `AppSidebar` 中添加 Drawer 做扩展    |

---

## 安全与维护

- 定期执行 `npm audit fix` 与依赖升级。
- 生产环境使用 HTTPS + 严格的 CORS + CSRF 保护（后端目前提供 JWT + CSRF header）。
- 若发现安全漏洞，请在 Issue 标注 `security`，并同步通知维护者。

如需更多帮助（例如新增 "注销账号" API、移动端适配等），欢迎提交 Issue 或 PR。

