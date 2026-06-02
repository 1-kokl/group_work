from app import create_app, db
from app.models.ca_models import Certificate

# 创建应用实例
app = create_app()

# 创建数据表
with app.app_context():
    db.create_all()
    print("✅ 证书表创建成功！")