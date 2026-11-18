from flask import Flask
from flask_restx import Api, Namespace
from app.api.user_api import user_bp
from app.api.auth_api import auth_bp
from app.api.admin_api import admin_bp
from app.api.tunnel_api import tunnel_bp

api = Api(
    title="用户认证API",
    version="1.0",
    description="实验八：符合RESTful规范的用户/认证接口",
    doc="/docs/"
)

user_ns = Namespace("user", description="用户管理")
auth_ns = Namespace("auth", description="认证管理")
api.add_namespace(user_ns, path="/api/v1")
api.add_namespace(auth_ns, path="/api/v1/auth")


def init_api(app: Flask):
    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(tunnel_bp)
    api.init_app(app)
