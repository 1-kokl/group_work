from flask import Flask
from app.extensions import db
from app.routes._init_ import register_blueprints
from app.api._init_ import init_api


def create_app():
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 配置数据库
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化扩展
    db.init_app(app)

    # 初始化API（注册auth和user蓝图）
    init_api(app)

    # 注册其他蓝图
    register_blueprints(app)

    return app
