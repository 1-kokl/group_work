from flask import Flask, send_from_directory
import os
from app.extensions import db
from app.routes import register_blueprints
from app.api._init_ import init_api


def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')
    
    db.init_app(app)
    
    register_blueprints(app)
    
    upload_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads'))
    os.makedirs(upload_folder, exist_ok=True)
    
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        print(f"[DEBUG] 请求文件: {filename}")
        print(f"[DEBUG] 完整路径: {os.path.join(upload_folder, filename)}")
        print(f"[DEBUG] 文件是否存在: {os.path.exists(os.path.join(upload_folder, filename))}")
        return send_from_directory(upload_folder, filename)
    
    with app.app_context():
        from app.models import ca_models, ecommerce_models
        db.create_all()
    
    return app
