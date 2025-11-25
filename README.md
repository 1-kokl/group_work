1.请将代码放在main分支下 


2.这是目录结构(点击查看)\n
project/ <br>
├── app/ <br>
│   ├── services/          # 已存放实验七的工具类（如RSAServices、JWTService等） <br>
│   ├── routes/            # 存放路由逻辑（从两个文件中拆分路由）<br>
│   │   ├── __init__.py<br>
│   │   ├── auth_routes.py  # 整合用户注册/登录/信息接口<br>
│   │   └── other_routes.py # 其他扩展接口（如实验七的数据库初始化）<br>
│   ├── models/            # 存放数据模型（实验七的SQLAlchemy模型）<br>
│   │   └── __init__.py<br>
│   └── __init__.py        # Flask应用初始化<br>
├── config.py              # 配置参数（避免硬编码） <br>
|—— swagger_config.py      #Swagger文档配置参数 <br>
└── run.py                 # 应用启动入口 <br>
|__ flask_new.py <br>

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

3.需要导入哪些包请记录在这里  

# Web框架及扩展  
pip install flask              # Flask核心框架 <br>
pip install flask-cors         # 处理跨域请求（代码中使用了CORS）<br>
pip install flask-restx        # 构建RESTful API并生成Swagger文档（app/api/__init__.py中使用）<br>

# 数据库相关<br>
pip install sqlalchemy         # ORM工具（数据模型和数据库操作，多处使用）<br>

# 加密与认证<br>
pip install pycryptodome       # 提供RSA加密功能（Crypto.PublicKey等模块）<br>
pip install pyjwt              # 处理JWT令牌生成与验证（JWTService中使用）<br>
