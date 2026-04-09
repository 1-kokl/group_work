from app import app, db

# 创建数据表
with app.app_context():
    db.create_all()
    print("✅ 证书表创建成功！")