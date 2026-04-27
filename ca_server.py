import datetime
from functools import wraps
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from sqlalchemy import create_engine, Column, BigInteger, String, DateTime, Integer, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.exceptions import InvalidSignature
import pytz
import os

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
#自动从 rootCA.crt 提取公钥
# ##############################
# 自动加载项目根目录的 CA 证书，提取公钥
CA_CERT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rootCA.crt")

try:
    # 读取CA证书文件 → 自动提取公钥
    with open(CA_CERT_PATH, "rb") as f:
        ca_cert = x509.load_pem_x509_certificate(f.read(), default_backend())
    ca_public_key = ca_cert.public_key()
    # 自动获取CA颁发者信息（和证书一致）
    CA_ISSUER = str(ca_cert.subject)
    print("✅ CA公钥加载成功！")
    print(f"✅ CA颁发者：{CA_ISSUER}")
except FileNotFoundError:
    raise RuntimeError(f"❌ 未找到CA证书文件，请将 rootCA.crt 放在项目根目录：{CA_CERT_PATH}")
except Exception as e:
    raise RuntimeError(f"❌ CA证书加载失败：{str(e)}")

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
# 核心：CA公钥验证证书签名（防伪造）
# ##############################
def verify_cert_signature(cert):
    try:
        ca_public_key.verify(
            cert.signature,
            cert.tbs_certificate_bytes,
            padding.PKCS1v15(),
            cert.signature_hash_algorithm
        )
        return True
    except InvalidSignature:
        return False
    except Exception:
        return False


# ##############################
# 登录接口
# ##############################
@app.route('/ca/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    if username == 'admin' and password == '123456':
        token = create_access_token(identity={"username": "admin", "role": "admin"})
        return jsonify(code=0, msg="success", token=token)
    return jsonify(code=401, msg="用户名或密码错误"), 401


# ##############################
# 证书吊销接口
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

    cert.status = 1
    cert.revoke_time = datetime.datetime.now()
    cert.revoke_reason = reason

    crl = CRL(serial_number=serial_number, revoke_time=cert.revoke_time, revoke_reason=reason)
    db.add(crl)
    db.commit()

    return jsonify(code=0, msg="证书吊销成功")


# ##############################
# 证书验证接口（完整CA公钥校验）
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

    serial_hex = f"{cert.serial_number:x}"
    now_utc = datetime.datetime.now(pytz.UTC)
    db_cert = db.query(Certificate).filter(Certificate.serial_number == serial_hex).first()

    result = {
        "serial_number": serial_hex,
        "valid": True,
        "expired": False,
        "revoked": False,
        "invalid_signature": False,
        "unauthorized_issuer": False,
        "not_registered": False
    }

    # 1. 验证签名（防伪造核心）
    if not verify_cert_signature(cert):
        result["valid"] = False
        result["invalid_signature"] = True

    # 2. 验证颁发者为本CA
    if str(cert.issuer) != CA_ISSUER:
        result["valid"] = False
        result["unauthorized_issuer"] = True

    # 3. 验证证书已备案
    if not db_cert:
        result["valid"] = False
        result["not_registered"] = True

    # 4. 验证有效期
    if now_utc < cert.not_valid_before or now_utc > cert.not_valid_after:
        result["valid"] = False
        result["expired"] = True

    # 5. 验证是否吊销
    if db_cert and db_cert.status == 1:
        result["valid"] = False
        result["revoked"] = True

    return jsonify(code=0, msg="验证完成", data=result)


# ##############################
# 上传证书接口
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
