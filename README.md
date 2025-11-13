1.请将代码放在main分支下 \n


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


3.需要导入哪些包请记录在这里  

# Web框架及扩展  \n
pip install flask              # Flask核心框架 <br>
pip install flask-cors         # 处理跨域请求（代码中使用了CORS）<br>
pip install flask-restx        # 构建RESTful API并生成Swagger文档（app/api/__init__.py中使用）<br>

# 数据库相关<br>
pip install sqlalchemy         # ORM工具（数据模型和数据库操作，多处使用）<br>

# 加密与认证<br>
pip install pycryptodome       # 提供RSA加密功能（Crypto.PublicKey等模块）<br>
pip install pyjwt              # 处理JWT令牌生成与验证（JWTService中使用）<br>
