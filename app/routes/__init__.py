from .cert_routes import cert_bp
from .ecommerce_routes import ecommerce_bp

def register_blueprints(app):
    """注册所有蓝图到 Flask 应用"""
    app.register_blueprint(cert_bp)
    app.register_blueprint(ecommerce_bp)
