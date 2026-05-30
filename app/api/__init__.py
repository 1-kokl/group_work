from flask import Flask
from flask_restx import Api, Namespace  # ✅ 修改1：导入 Namespace
from app.api.user_api import user_bp
from app.api.auth_api import auth_bp

# 初始化API文档
api = Api(
    title="用户认证API",
    version="1.0",
    description="实验八：符合RESTful规范的用户/认证接口",
    doc="/docs/"  # 文档访问路径：http://localhost:5000/docs
)

# ====================== ✅ 修改2：创建 Namespace 代替 Blueprint ======================
# 因为 api.add_namespace 只能接收 Namespace，不能接收 Blueprint
user_ns = Namespace('user', description='用户管理')
auth_ns = Namespace('auth', description='认证管理')

# 注册命名空间到文档
api.add_namespace(user_ns, path="/api/v1")
api.add_namespace(auth_ns, path="/api/v1/auth")

def init_api(app: Flask):
    """在run.py中调用，注册所有接口"""
    app.register_blueprint(user_bp)    # 这行保留
    app.register_blueprint(auth_bp)    # 这行保留
    api.init_app(app)                  # 这行保留