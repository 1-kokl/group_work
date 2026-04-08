import datetime
from functools import wraps
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from sqlalchemy import create_engine, Column, BigInteger, String, DateTime, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

app = Flask(__name__)

# JWT 配置
app.config['JWT_SECRET_KEY'] = 'ca-server-secret-2025'
jwt = JWTManager(app)

# 数据库初始化
SQLALCHEMY_DATABASE_URL = "sqlite:///./ca.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ##############################
# 数据库表模型
# ##############################
class Certificate(Base):
    __tablename__ = "ca_certificate"

    id = Column(BigInteger, primary_key=True, index=True)
    serial_number = Column(String(64), unique=True, index=True, comment="证书序列号")
    subject = Column(String(255), comment="主题")
    issuer = Column(String(255), comment="颁发者")
    cert_data = Column(Text, comment="证书PEM内容")
    valid_from = Column(DateTime, comment="生效时间")
    valid_to = Column(DateTime, comment="过期时间")
    status = Column(Integer, default=0, comment="0正常 1吊销 2过期")
    revoke_time = Column(DateTime, nullable=True)
    revoke_reason = Column(String(100), nullable=True)
    create_time = Column(DateTime, default=datetime.datetime.now)
    update_time = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)


class CRL(Base):
    __tablename__ = "ca_crl"
    id = Column(BigInteger, primary_key=True)
    serial_number = Column(String(64), index=True)
    revoke_time = Column(DateTime)
    revoke_reason = Column(String(100))


Base.metadata.create_all(bind=engine)


# ##############################
# 工具方法
# ##############################
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        identity = get_jwt_identity()
        if identity.get('role') != 'admin':
            return jsonify({"code": 403, "msg": "需要管理员权限"}), 403
        return fn(*args, **kwargs)

    return wrapper


# 解析PEM证书
def parse_cert(pem_data):
    try:
        cert = x509.load_pem_x509_certificate(pem_data.encode(), default_backend())
        return cert
    except Exception as e:
        return None


# ##############################
# 登录接口（获取token）
# ##############################
@app.route('/ca/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    # 简单模拟管理员
    if username == 'admin' and password == '123456':
        token = create_access_token(identity={"username": "admin", "role": "admin"})
        return jsonify(code=0, msg="success", token=token)
    return jsonify(code=401, msg="用户名或密码错误"), 401


# ##############################
# 3. 证书吊销接口（管理员权限）
# ##############################
@app.route('/ca/revoke', methods=['POST'])
@admin_required
def revoke_cert():
    db = next(get_db())
    serial_number = request.json.get('serial_number')
    reason = request.json.get('reason', 'unspecified')

    cert = db.query(Certificate).filter(Certificate.serial_number == serial_number).first()
    if not cert:
        return jsonify(code=404, msg="证书不存在")

    if cert.status == 1:
        return jsonify(code=400, msg="证书已吊销")

    # 更新证书状态
    cert.status = 1
    cert.revoke_time = datetime.datetime.now()
    cert.revoke_reason = reason

    # 加入CRL
    crl = CRL(
        serial_number=serial_number,
        revoke_time=cert.revoke_time,
        revoke_reason=reason
    )
    db.add(crl)
    db.commit()

    return jsonify(code=0, msg="证书吊销成功")


# ##############################
# 4. 证书验证接口
# ##############################
@app.route('/ca/verify', methods=['POST'])
def verify_cert():
    db = next(get_db())
    cert_pem = request.json.get('cert_pem')
    if not cert_pem:
        return jsonify(code=400, msg="缺少证书PEM")

    cert = parse_cert(cert_pem)
    if not cert:
        return jsonify(code=400, msg="证书格式错误")

    serial = cert.serial_number
    serial_hex = f"{serial:x}"

    # 查询数据库
    db_cert = db.query(Certificate).filter(Certificate.serial_number == serial_hex).first()
    now = datetime.datetime.now()

    result = {
        "serial_number": serial_hex,
        "valid": True,
        "expired": False,
        "revoked": False,
        "valid_from": cert.not_valid_before.replace(tzinfo=None).isoformat(),
        "valid_to": cert.not_valid_after.replace(tzinfo=None).isoformat()
    }

    # 过期检查
    if now < cert.not_valid_before.replace(tzinfo=None) or now > cert.not_valid_after.replace(tzinfo=None):
        result["valid"] = False
        result["expired"] = True

    # 吊销检查
    if db_cert and db_cert.status == 1:
        result["valid"] = False
        result["revoked"] = True

    return jsonify(code=0, msg="验证完成", data=result)


# ##############################
# 上传证书接口（管理员）
# ##############################
@app.route('/ca/cert', methods=['POST'])
@admin_required
def add_cert():
    db = next(get_db())
    cert_pem = request.json.get('cert_pem')
    cert = parse_cert(cert_pem)
    if not cert:
        return jsonify(code=400, msg="证书无效")

    serial_hex = f"{cert.serial_number:x}"

    new_cert = Certificate(
        serial_number=serial_hex,
        subject=str(cert.subject),
        issuer=str(cert.issuer),
        cert_data=cert_pem,
        valid_from=cert.not_valid_before.replace(tzinfo=None),
        valid_to=cert.not_valid_after.replace(tzinfo=None)
    )
    db.add(new_cert)
    db.commit()
    return jsonify(code=0, msg="证书入库成功", serial_number=serial_hex)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)
