1.请将代码放在main分支下


2.这是目录结构
project/
├── app/
│   ├── services/          # 已存放实验七的工具类（如RSAServices、JWTService等）
│   ├── routes/            # 存放路由逻辑（从两个文件中拆分路由）
│   │   ├── __init__.py
│   │   ├── auth_routes.py  # 整合用户注册/登录/信息接口
│   │   └── other_routes.py # 其他扩展接口（如实验七的数据库初始化）
│   ├── models/            # 存放数据模型（实验七的SQLAlchemy模型）
│   │   └── __init__.py
│   └── __init__.py        # Flask应用初始化
├── config.py              # 配置参数（避免硬编码）
└── run.py                 # 应用启动入口
|__ flask_new.py
