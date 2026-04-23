# CA 证书认证平台 - 基于国密算法的强身份认证系统

## 📖 项目介绍

本项目是一个基于 **Flask + Vue 3** 的全栈应用，实现了基于数字证书的强身份认证系统。系统采用国密算法（SM2/SM3/SM4）进行数据加密和签名，支持 X.509 证书的签发、管理和验证，提供完整的证书生命周期管理功能。

### 核心特性

- 🔐 **基于证书的强身份认证**：支持 X.509 客户端证书登录
- 🇨🇳 **国密算法支持**：集成 SM2（非对称加密）、SM3（哈希）、SM4（对称加密）
- 🎫 **完整的证书管理**：证书签发、下载、合并、验证、吊销
- 🔑 **JWT 令牌认证**：证书验证通过后颁发 JWT Token
- 🌐 **前后端分离架构**：RESTful API 设计，Vue 3 前端界面
- 📊 **Swagger API 文档**：自动生成接口文档
- 🛡️ **多层安全防护**：输入验证、密码加密、CSRF 防护

### 技术亮点

1. **双因素认证机制**：证书认证 + JWT Token
2. **证书链验证**：CA 根证书签名验证 + 有效期检查 + 数据库指纹匹配
3. **密钥安全管理**：私钥本地生成，证书在线签发
4. **响应式设计**：支持桌面端和移动端访问

---

## 🏗️ 项目架构

### 后端技术栈

- **Web 框架**：Flask 3.1.3
- **ORM**：SQLAlchemy 2.0.49 + Flask-SQLAlchemy
- **API 文档**：Flask-RESTx 1.3.2 + Swagger UI
- **加密库**：cryptography 46.0.7 + gmssl 3.2.2
- **认证**：Flask-JWT-Extended 4.7.1
- **跨域**：Flask-CORS 6.0.2
- **数据库**：SQLite（可扩展至 MySQL/PostgreSQL）

### 前端技术栈

- **框架**：Vue 3.4.0
- **UI 组件库**：Element Plus 2.7.8
- **状态管理**：Vuex 4.1.0
- **路由**：Vue Router 4.3.0
- **HTTP 客户端**：Axios 1.7.0
- **国密算法**：sm-crypto 0.4.0
- **测试框架**：Jest + Cypress + Testing Library
- **Mock 服务**：MSW (Mock Service Worker)

---

## 📁 项目结构
---
group_work-main/
├── app/ # 后端应用目录
│ ├── api/ # API 路由定义
│ │ ├── auth_api.py # 认证相关接口
│ │ └── user_api.py # 用户管理接口
│ ├── middleware/ # 中间件
│ │ └── jwt_auth.py # JWT 认证中间件
│ ├── models/ # 数据模型
│ │ └── ca_models.py # 证书相关模型
│ ├── routes/ # 业务路由
│ │ └── cert_routes.py # 证书管理路由
│ ├── services/ # 业务逻辑层
│ │ ├── cert_service.py # 证书签发与验证服务
│ │ ├── user_service.py # 用户管理服务
│ │ ├── SM2_Utils.py # SM2 非对称加密工具
│ │ ├── SM3_Service.py # SM3 哈希服务
│ │ ├── SM4_Utils.py # SM4 对称加密工具
│ │ └── JWT_SM2_Utils.py # JWT + SM2 签名工具
│ ├── utils/ # 工具函数
│ │ ├── jwt_util.py # JWT 工具
│ │ └── response.py # 统一响应格式
│ ├── sm2_key.txt # SM2 私钥文件
│ └── sm4_key.txt # SM4 密钥文件
├── certs/ # CA 证书目录
│ ├── rootCA.crt # CA 根证书
│ └── rootCA.key # CA 私钥
├── ecommerce-frontend/ # 前端项目目录
│ ├── src/
│ │ ├── components/ # 公共组件
│ │ ├── pages/ # 页面组件
│ │ │ ├── auth/ # 认证页面（登录/注册/证书登录）
│ │ │ ├── cert/ # 证书管理页面
│ │ │ ├── dashboard/ # 仪表板
│ │ │ ├── navigation/ # 系统导航
│ │ │ └── user/ # 用户中心
│ │ ├── router/ # 路由配置
│ │ ├── services/ # API 服务
│ │ │ ├── api/ # API 封装
│ │ │ ├── certAuth.js # 证书认证服务
│ │ │ └── http.js # HTTP 客户端
│ │ ├── store/ # Vuex 状态管理
│ │ │ └── modules/ # 模块化状态
│ │ ├── utils/ # 工具函数
│ │ │ ├── crypto.js # 加密工具
│ │ │ ├── sm_crypto.js # 国密算法封装
│ │ │ └── security.js # 安全校验
│ │ ├── App.vue # 根组件
│ │ └── main.js # 入口文件
│ ├── tests/ # 测试文件
│ ├── package.json # 前端依赖配置
│ └── vue.config.js # Vue 配置
├── run.py # 后端启动入口
├── requirements.txt # Python 依赖
├── user.db # SQLite 数据库
└── Nginx配置.pl # Nginx 配置示例


## 🚀 当前进度

### ✅ 已完成功能

#### 后端功能
- [x] 用户注册与登录（用户名/密码）
- [x] JWT Token 生成与验证
- [x] CA 根证书生成与管理
- [x] 用户证书签发（RSA 2048 + SHA256）
- [x] 证书验证接口（CA 签名验证 + 有效期检查）
- [x] 证书登录接口（`/api/cert/cert-login`）
- [x] 证书数据库存储（指纹、序列号、状态）
- [x] 国密算法集成（SM2/SM3/SM4）
- [x] 用户信息管理（查询、更新手机号）
- [x] Token 刷新机制
- [x] Swagger API 文档自动生成

#### 前端功能
- [x] 用户注册页面
- [x] 用户登录页面
- [x] 证书登录页面（支持文件上传）
- [x] 系统导航页面
- [x] 个人中心页面
- [x] 证书管理中心
- [x] 证书下载与合并
- [x] CSR 生成页面
- [x] 根证书下载
- [x] 路由守卫（登录验证）
- [x] Axios 拦截器（Token 自动携带）
- [x] 401 自动刷新 Token
- [x] 响应式布局（支持移动端）
- [x] 单元测试与 E2E 测试框架

### ⚠️ 待完善功能

#### 高优先级
- [ ] Nginx mTLS 配置（双向 SSL 认证）
- [ ] 前端浏览器端密钥对生成（Web Crypto API）
- [ ] 证书吊销功能（CRL/OCSP）
- [ ] 证书续期功能
- [ ] 批量证书管理

#### 中优先级
- [ ] 证书使用审计日志
- [ ] 多 CA 支持
- [ ] 证书模板管理
- [ ] 邮件通知（证书即将过期）
- [ ] 管理员后台


---

## 📦 安装依赖

### 环境要求

- **Python**: >= 3.8
- **Node.js**: >= 14.0.0
- **npm**: >= 6.0.0
- **操作系统**: Windows / Linux / macOS

### 后端依赖安装

#### 方式一：使用 requirements.txt（推荐）
进入项目根目录
cd group_work-main
创建虚拟环境（推荐）
python -m venv venv
激活虚拟环境
Windows:
venv\Scripts\activate
Linux/Mac:
source venv/bin/activate
安装所有依赖
pip install -r requirements.txt
#### 方式二：手动安装
Web 框架及扩展
pip install flask==3.1.3 pip install flask-cors==6.0.2 pip install flask-restx==1.3.2 pip install flask-swagger-ui==5.32.2
数据库相关
pip install sqlalchemy==2.0.49 pip install flask-sqlalchemy==3.1.1
加密与认证
pip install cryptography==46.0.7 pip install gmssl==3.2.2 pip install flask-jwt-extended==4.7.1
其他工具
pip install pytz==2025.1
### 前端依赖安装
进入前端目录
cd ecommerce-frontend
安装依赖
npm install
或使用 yarn
yarn install
代码格式化
pip install black pip install flake8
前端代码检查
npm run lint---

## 🔧 快速开始

### 1. 初始化数据库
首次运行会自动创建数据库和表
python run.py
### 2. 启动后端服务
方式一：使用 run.py（同时启动命令行菜单）
python run.py
方式二：仅启动 Flask 服务
python -c "from run import app; app.run(host='0.0.0.0', port=5000)"
后端服务将在 `http://localhost:5000` 启动

### 3. 启动前端开发服务器

cd ecommerce-frontend 
npm run serve
前端开发服务器将在 `http://localhost:8080` 启动

### 4. 访问应用

- **前端界面**: http://localhost:8080
- **API 文档**: http://localhost:5000/docs/
- **后端健康检查**: http://localhost:5000/api/health

---

## 📝 API 接口说明

### 认证接口

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| POST | `/api/v1/auth/login` | 用户登录 | ❌ |
| POST | `/api/v1/auth/register` | 用户注册 | ❌ |
| POST | `/api/v1/auth/refresh` | 刷新 Token | ❌ |
| POST | `/api/v1/auth/logout` | 注销登录 | ✅ |

### 证书接口

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| GET | `/api/cert/ca` | 获取 CA 根证书 | ❌ |
| POST | `/api/cert/issue` | 签发用户证书 | ✅ |
| POST | `/api/cert/cert-login` | 证书登录 | ❌ |
| GET | `/api/cert/get` | 获取用户证书 | ✅ |
| POST | `/api/cert/test` | 测试证书格式 | ❌ |
| POST | `/api/cert/merge` | 合并证书链 | ❌ |

### 用户接口

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| GET | `/api/v1/users/me` | 获取当前用户信息 | ✅ |
| PATCH | `/api/v1/users/me/phone` | 更新手机号 | ✅ |

> 详细 API 文档请访问：http://localhost:5000/docs/

---

## 🔐 证书认证流程

### 首次使用流程

1. **用户注册** → 创建账号
2. **申请证书** → 调用 `/api/cert/issue` 接口
3. **下载证书** → 保存 `.pem` 或 `.crt` 文件
4. **证书登录** → 访问 `/login/certificate` 上传证书
5. **验证通过** → 获得 JWT Token
6. **访问系统** → 使用 Token 访问受保护资源

### 证书验证机制

用户上传证书 
↓ 解析证书内容
↓ 验证 CA 签名（确保由本平台签发）
↓ 检查有效期（未过期且已生效）
↓ 查询数据库（指纹匹配 + 状态检查）
↓ 验证通过 → 生成 JWT Token
↓ 返回 Token 给前端




