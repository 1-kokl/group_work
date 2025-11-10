from flask import Flask
from flask_restx import Api
from app.api.user_api import user_bp
from app.api.auth_api import auth_bp

# 初始化API文档
api = Api(
    title="用户认证API",
    version="1.0",
    description="实验八：符合RESTful规范的用户/认证接口",
    doc="/docs/"  # 文档访问路径：http://localhost:5000/docs
)

# 注册接口蓝图到文档
api.add_namespace(user_bp, path="/api/v1")
api.add_namespace(auth_bp, path="/api/v1/auth")

def init_api(app: Flask):
    """在run.py中调用，注册所有接口"""
    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)
    api.init_app(app)