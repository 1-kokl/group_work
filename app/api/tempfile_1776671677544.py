from .cert_routes import cert_bp

def register_blueprints(app):
    """注册所有蓝图到 Flask 应用"""
    app.register_blueprint(cert_bp)
