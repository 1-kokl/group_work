from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# 1. 创建Flask应用对象
app = Flask(__name__)

# 2. 数据库配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ca_cert.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '123456'

# 3. 创建数据库对象
db = SQLAlchemy(app)

# 4. 注册证书蓝图
from app.routes.cert_routes import cert_bp
app.register_blueprint(cert_bp)