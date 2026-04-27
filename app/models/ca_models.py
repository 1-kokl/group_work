# 导入db（现在100%不报红）
from app import db
from datetime import datetime
import uuid


class Certificate(db.Model):
    __tablename__ = "certificates"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.BigInteger, nullable=False, comment="绑定用户ID")
    fingerprint = db.Column(db.String(128), unique=True, nullable=False, comment="证书指纹")
    serial_number = db.Column(db.String(64), unique=True, nullable=False, comment="证书序列号")
    subject = db.Column(db.String(256), nullable=False, comment="证书主题")
    cert_type = db.Column(db.String(20), nullable=False, comment="client/merchant")
    status = db.Column(db.Boolean, default=True, comment="证书状态")
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    expired_at = db.Column(db.DateTime, nullable=False)