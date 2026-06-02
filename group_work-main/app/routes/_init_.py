from flask import Blueprint

from .cert_routes import cert_bp
from .ecommerce_routes import ecommerce_bp
from .payment_routes import pay_bp

def register_blueprints(app):
    app.register_blueprint(cert_bp)
    app.register_blueprint(ecommerce_bp)
    app.register_blueprint(pay_bp)
