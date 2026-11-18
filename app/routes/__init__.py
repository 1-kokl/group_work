from flask import Flask
from .cert_routes import cert_bp
from .ecommerce_routes import ecommerce_bp
from .payment_routes import pay_bp


def register_blueprints(app: Flask):
    """注册所有蓝图"""
    app.register_blueprint(cert_bp)
    app.register_blueprint(ecommerce_bp)
    app.register_blueprint(pay_bp)


__all__ = [
    'cert_bp',
    'ecommerce_bp',
    'pay_bp',
    'register_blueprints'
]
