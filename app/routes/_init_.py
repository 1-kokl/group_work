from flask import Blueprint

from .cert_routes import cert_bp

def register_blueprints(app):
    app.register_blueprint(cert_bp)