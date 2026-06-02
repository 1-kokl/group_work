from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import logging
from datetime import datetime, timedelta
import json
import base64
import random
import re
import time
import string
import os
import subprocess
import gmssl
from gmssl import sm2, sm3, sm4

# ========== 1. 日志配置（保留原逻辑） ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_security.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ========== 2. 数据库配置（保留原多数据库适配逻辑） ==========
def create_db_engine(db_type="sqlite", **kwargs):
    """多数据库引擎创建（保留原逻辑）"""
    if db_type == "sqlite":
        db_path = kwargs.get("db_path", "ecommerce.db")
        engine = create_engine(
            f"sqlite:///{db_path}",
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=3600,
            echo=False
        )
    elif db_type == "mysql":
        host = kwargs.get("host", "localhost")
        port = kwargs.get("port", 3306)
        user = kwargs.get("user", "root")
        password = kwargs.get("password", "123456")
        db = kwargs.get("db", "ecommerce")
        engine = create_engine(
            f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8mb4",
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=3600,
            echo=False
        )
    elif db_type == "postgresql":
        host = kwargs.get("host", "localhost")
        port = kwargs.get("port", 5432)
        user = kwargs.get("user", "postgres")
        password = kwargs.get("password", "123456")
        db = kwargs.get("db", "ecommerce")
        engine = create_engine(
            f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}",
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=3600,
            echo=False
        )
    else:
        raise ValueError(f"不支持的数据库类型：{db_type}")
    return engine


# 默认SQLite引擎（保留原逻辑）
engine = create_db_engine("sqlite")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ========== 3. 数据库会话工具（保留原逻辑） ==========
def get_db_session():
    """获取数据库会话（自动回收）"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"数据库会话异常：{e}")
        db.rollback()
        raise
    finally:
        db.close()


# ========== 4. 国密算法工具类（替换原RSA工具类） ==========
# ================= SM2 非对称加密/签名 =================
class SM2Service:
    def __init__(self):
        # 初始化SM2（国密推荐曲线）
        self.sm2_crypt = sm2.CryptSM2(
            public_key=None,
            private_key=None,
            curve="sm2p256v1"
        )
        # 加载/生成SM2密钥对
        self.private_key, self.public_key = self.load_or_generate_keys()

    def load_or_generate_keys(self):
        """加载SM2密钥对，无则生成并保存（替换原RSA密钥加载）"""
        # 确保app目录存在
        if not os.path.exists("app"):
            os.makedirs("app")
        try:
            # 读取SM2私钥/公钥文件
            with open("app/sm2_private_key.pem", "r", encoding="utf-8") as f:
                private_key = f.read().strip()
            with open("app/sm2_public_key.pem", "r", encoding="utf-8") as f:
                public_key = f.read().strip()
            # 验证密钥有效性
            self.sm2_crypt.set_private_key(private_key)
            self.sm2_crypt.set_public_key(public_key)
            logger.info("✅ SM2密钥对加载成功")
            return private_key, public_key
        except Exception as e:
            logger.error(f"❌ SM2密钥加载失败：{e}，生成新密钥对")
            # 生成新密钥对（替换原RSA密钥生成）
            private_key = self.sm2_crypt.generate_private_key()
            public_key = self.sm2_crypt.generate_public_key(private_key)
            # 保存密钥到文件
            with open("app/sm2_private_key.pem", "w", encoding="utf-8") as f:
                f.write(private_key)
            with open("app/sm2_public_key.pem", "w", encoding="utf-8") as f:
                f.write(public_key)
            logger.info("✅ SM2新密钥对已生成并保存")
            return private_key, public_key

    def encrypt(self, plain_text):
        """SM2公钥加密（替换原RSA加密，方法名/入参/出参完全一致）"""
        if not isinstance(plain_text, str):
            plain_text = str(plain_text)
        self.sm2_crypt.set_public_key(self.public_key)
        # 国密SM2加密（C1C2C3模式）
        cipher_bytes = self.sm2_crypt.encrypt(plain_text.encode("utf-8"), mode=1)
        return base64.b64encode(cipher_bytes).decode("utf-8")

    def decrypt(self, cipher_base64):
        """SM2私钥解密（替换原RSA解密，方法名/入参/出参完全一致）"""
        self.sm2_crypt.set_private_key(self.private_key)
        # Base64解码→SM2解密
        cipher_bytes = base64.b64decode(cipher_base64)
        plain_bytes = self.sm2_crypt.decrypt(cipher_bytes, mode=1)
        return plain_bytes.decode("utf-8")

    def sign(self, data):
        """SM2签名（替换原RSA签名，用于JWT）"""
        if not isinstance(data, str):
            data = str(data)
        self.sm2_crypt.set_private_key(self.private_key)
        # 生成随机数（SM2签名必需）
        random_hex = hex(random.randint(1, 10 ** 64))[2:]
        sign_bytes = self.sm2_crypt.sign(data.encode("utf-8"), random_hex)
        return base64.b64encode(sign_bytes).decode("utf-8")

    def verify(self, data, sign_base64):
        """SM2验签（替换原RSA验签，用于JWT）"""
        if not isinstance(data, str):
            data = str(data)
        self.sm2_crypt.set_public_key(self.public_key)
        sign_bytes = base64.b64decode(sign_base64)
        return self.sm2_crypt.verify(sign_bytes, data.encode("utf-8"))

    def encrypt_large_data(self, info):
        """SM2分片加密（替换原RSA分片加密，方法名/逻辑一致）"""
        if not isinstance(info, str):
            info = str(info)
        max_chunk_size = 64  # SM2推荐分片大小
        chunks = [info[i:i + max_chunk_size] for i in range(0, len(info), max_chunk_size)]
        encrypted_chunks = [self.encrypt(chunk) for chunk in chunks]
        return base64.b64encode(json.dumps(encrypted_chunks).encode()).decode()

    def decrypt_large_data(self, encrypted_data):
        """SM2分片解密（替换原RSA分片解密，方法名/逻辑一致）"""
        encrypted_chunks = json.loads(base64.b64decode(encrypted_data).decode())
        decrypted_chunks = [self.decrypt(chunk) for chunk in encrypted_chunks]
        return "".join(decrypted_chunks)

    def rotate_keys(self):
        """SM2密钥轮换（替换原RSA密钥轮换，逻辑一致）"""
        old_private = self.private_key
        old_public = self.public_key
        # 生成新密钥
        self.generate_keys()
        # 备份旧密钥
        backup_suffix = datetime.now().strftime("%Y%m%d%H%M%S")
        with open(f"app/sm2_private_key_backup_{backup_suffix}.pem", "w", encoding="utf-8") as f:
            f.write(old_private)
        with open(f"app/sm2_public_key_backup_{backup_suffix}.pem", "w", encoding="utf-8") as f:
            f.write(old_public)
        logger.info("✅ SM2密钥轮换完成，旧密钥已备份")

    def generate_keys(self):
        """独立生成SM2密钥对（兼容原RSA方法名）"""
        self.private_key = self.sm2_crypt.generate_private_key()
        self.public_key = self.sm2_crypt.generate_public_key(self.private_key)
        with open("app/sm2_private_key.pem", "w", encoding="utf-8") as f:
            f.write(self.private_key)
        with open("app/sm2_public_key.pem", "w", encoding="utf-8") as f:
            f.write(self.public_key)


# ================= SM3 哈希算法（替换SHA256） =================
class SM3Service:
    @staticmethod
    def hash(data, salt=""):
        """SM3哈希（替换原SHA256，方法名/入参/出参完全一致）"""
        if not isinstance(data, str):
            data = str(data)
        # 拼接盐值（保留原加盐逻辑）
        data_with_salt = f"{data}{salt}"
        # 国密SM3哈希计算
        return sm3.sm3_hash(data_with_salt.encode("utf-8"))

    @staticmethod
    def verify_hash(plain_data, hash_value, salt=""):
        """验证SM3哈希（替换原SHA256验证，逻辑一致）"""
        return SM3Service.hash(plain_data, salt) == hash_value


# ================= SM4 对称加密（可选，补充国密能力） =================
class SM4Service:
    def __init__(self, key=None):
        # SM4密钥固定16字节（国密标准）
        self.key = key if key else bytes(random.choices(range(256), k=16))
        self.sm4_crypt = sm4.CryptSM4()

    def encrypt(self, plain_text, iv=None):
        """SM4-CBC加密（补充对称加密能力）"""
        if not isinstance(plain_text, str):
            plain_text = str(plain_text)
        # 初始化向量（CBC模式必需，16字节）
        iv = iv if iv else bytes(random.choices(range(256), k=16))
        self.sm4_crypt.set_key(self.key, sm4.SM4_ENCRYPT)
        # PKCS7补位（国密标准）
        plain_bytes = plain_text.encode("utf-8")
        pad_len = 16 - (len(plain_bytes) % 16)
        plain_bytes += bytes([pad_len] * pad_len)
        # 加密
        cipher_bytes = self.sm4_crypt.crypt_cbc(iv, plain_bytes)
        # 返回：iv+密文的Base64（方便解密）
        return base64.b64encode(iv + cipher_bytes).decode("utf-8")

    def decrypt(self, cipher_base64):
        """SM4-CBC解密（补充对称加密能力）"""
        cipher_all = base64.b64decode(cipher_base64)
        # 拆分iv和密文
        iv = cipher_all[:16]
        cipher_bytes = cipher_all[16:]
        self.sm4_crypt.set_key(self.key, sm4.SM4_DECRYPT)
        # 解密
        plain_bytes = self.sm4_crypt.crypt_cbc(iv, cipher_bytes)
        # 去补位
        pad_len = plain_bytes[-1]
        plain_bytes = plain_bytes[:-pad_len]
        return plain_bytes.decode("utf-8")


# ========== 5. 国密JWT工具类（替换原RS256-JWT） ==========
class SM2JWTService:
    def __init__(self):
        self.sm2 = SM2Service()  # 替换原RSA依赖
        self.expire_access = 2 * 3600  # 保留原过期时间
        self.expire_refresh = 7 * 24 * 3600
        # 保留原Token黑名单/缓存逻辑
        self.token_blacklist = set()
        self.refresh_token_cache = {}

    def generate_token(self, username, role):
        """生成SM2签名的JWT（替换原RS256-JWT，返回格式一致）"""
        # 保留原Payload结构
        access_payload = {
            "username": username,
            "role": role,
            "exp": int(time.time()) + self.expire_access,
            "iat": int(time.time()),
            "jti": str(random.randint(100000, 999999)),
            "type": "access"
        }
        refresh_payload = {
            "username": username,
            "exp": int(time.time()) + self.expire_refresh,
            "iat": int(time.time()),
            "jti": str(random.randint(100000, 999999)),
            "type": "refresh"
        }
        # Payload序列化（保留原逻辑）
        access_payload_str = json.dumps(access_payload, separators=(",", ":"))
        refresh_payload_str = json.dumps(refresh_payload, separators=(",", ":"))
        # SM2签名（替换原RSA签名）
        access_sign = self.sm2.sign(access_payload_str)
        refresh_sign = self.sm2.sign(refresh_payload_str)
        # 组装JWT（保留原格式：payload.base64.sign）
        access_token = f"{base64.b64encode(access_payload_str.encode()).decode()}.{access_sign}"
        refresh_token = f"{base64.b64encode(refresh_payload_str.encode()).decode()}.{refresh_sign}"
        # 缓存刷新token（保留原逻辑）
        self.refresh_token_cache[refresh_payload["jti"]] = {
            "username": username,
            "exp": refresh_payload["exp"],
            "token": refresh_token
        }
        return {"access_token": access_token, "refresh_token": refresh_token}

    def verify_token(self, token):
        """验证SM2-JWT（替换原RS256验证，返回格式一致）"""
        # 保留原黑名单逻辑
        if token in self.token_blacklist:
            return False, "❌ Token已被拉黑"
        try:
            # 拆分Payload和签名（保留原格式）
            payload_base64, sign_base64 = token.split(".", 1)
            # 解码Payload（保留原逻辑）
            payload_str = base64.b64decode(payload_base64).decode("utf-8")
            payload = json.loads(payload_str)
            # 验证过期时间
            if payload.get("exp", 0) < int(time.time()):
                return False, "❌ Token已过期，请重新登录"
            # 验证Token类型
            if payload.get("type") != "access":
                return False, "❌ 无效的Token类型（仅支持access令牌）"
            # SM2验签（替换原RSA验签）
            if not self.sm2.verify(payload_str, sign_base64):
                return False, "❌ Token签名验证失败"
            return True, payload
        except Exception as e:
            logger.error(f"Token验证异常：{e}")
            return False, f"❌ Token验证失败：{str(e)}"

    def refresh_access_token(self, refresh_token):
        """刷新access token（保留原逻辑，替换签名算法）"""
        try:
            # 拆分refresh token
            payload_base64, sign_base64 = refresh_token.split(".", 1)
            payload_str = base64.b64decode(payload_base64).decode("utf-8")
            payload = json.loads(payload_str)

            # 验证refresh token有效性
            if payload.get("type") != "refresh":
                return False, "❌ 无效的刷新令牌类型"
            if payload.get("exp", 0) < int(time.time()):
                return False, "❌ 刷新令牌已过期"
            if not self.sm2.verify(payload_str, sign_base64):
                return False, "❌ 刷新令牌签名验证失败"

            # 生成新的access token
            new_access_token = self.generate_token(payload["username"], payload.get("role", "buyer"))["access_token"]
            return True, new_access_token
        except Exception as e:
            logger.error(f"刷新Token异常：{e}")
            return False, f"❌ 刷新Token失败：{str(e)}"

    def blacklist_token(self, token):
        """拉黑Token（保留原逻辑）"""
        try:
            payload_base64, _ = token.split(".", 1)
            payload_str = base64.b64decode(payload_base64).decode("utf-8")
            payload = json.loads(payload_str)
            self.token_blacklist.add(token)
            # 清理刷新token缓存
            if payload.get("jti") in self.refresh_token_cache:
                del self.refresh_token_cache[payload["jti"]]
            logger.info(f"Token {payload['jti']} 已加入黑名单")
            return True
        except Exception as e:
            logger.error(f"拉黑Token失败：{e}")
            return False


# ========== 6. 数据模型定义（完全保留原结构，仅替换加密字段的算法调用） ==========
class User(Base):
    __tablename__ = "users"
    username = Column(String(50), primary_key=True)
    password_hash = Column(String(100), nullable=False)  # SM3哈希+盐值（替换原SHA256）
    fail_count = Column(Integer, default=0)
    last_fail_time = Column(Float, default=0)
    role = Column(String(20), nullable=False, default="buyer")
    phone = Column(String(20), nullable=False)  # 明文（内部查询）
    phone_encrypted = Column(String(200), nullable=False)  # SM2加密手机号（替换原RSA）
    email = Column(String(100), nullable=True)
    email_encrypted = Column(String(200), nullable=True)  # SM2加密邮箱（替换原RSA）
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = Column(Boolean, default=True)
    is_locked = Column(Boolean, default=False)

    # 关联关系
    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user")
    payments = relationship("Payment", back_populates="user")


class Address(Base):
    __tablename__ = "addresses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), ForeignKey("users.username"), nullable=False)
    receiver = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=False)
    phone_encrypted = Column(String(200), nullable=False)  # SM2加密（替换原RSA）
    province = Column(String(20), nullable=False)
    city = Column(String(20), nullable=False)
    district = Column(String(20), nullable=False)
    detail = Column(String(200), nullable=False)
    is_default = Column(Boolean, default=False)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联关系
    user = relationship("User", back_populates="addresses")


class Order(Base):
    __tablename__ = "orders"
    order_id = Column(String(32), primary_key=True)
    username = Column(String(50), ForeignKey("users.username"), nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    create_time = Column(DateTime, default=datetime.now)
    pay_time = Column(DateTime, nullable=True)
    ship_time = Column(DateTime, nullable=True)
    deliver_time = Column(DateTime, nullable=True)
    cancel_time = Column(DateTime, nullable=True)
    # SM2加密敏感字段（替换原RSA）
    receiver_phone_encrypted = Column(String(200), nullable=False)
    receiver_address_encrypted = Column(String(500), nullable=False)

    # 关联关系
    user = relationship("User", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="order", uselist=False)


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(32), ForeignKey("orders.order_id"), nullable=False)
    product_id = Column(String(32), nullable=False)
    product_name = Column(String(100), nullable=False)
    product_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    subtotal = Column(Float, nullable=False)

    # 关联关系
    order = relationship("Order", back_populates="order_items")


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(32), ForeignKey("orders.order_id"), nullable=False)
    username = Column(String(50), ForeignKey("users.username"), nullable=False)
    pay_amount = Column(Float, nullable=False)
    pay_method = Column(String(20), nullable=False)
    pay_time = Column(DateTime, default=datetime.now)
    # SM2加密敏感支付信息（替换原RSA）
    card_number_encrypted = Column(String(200), nullable=True)
    alipay_account_encrypted = Column(String(200), nullable=True)
    transaction_id = Column(String(100), nullable=True)

    # 关联关系
    user = relationship("User", back_populates="payments")
    order = relationship("Order", back_populates="payment")


# ========== 7. 核心业务服务类（保留原逻辑，仅替换加密算法调用） ==========
class DataSecurityService:
    def __init__(self):
        # 初始化国密工具类（替换原RSA/JWT）
        self.sm2 = SM2Service()
        self.sm3 = SM3Service()
        self.sm4 = SM4Service()
        self.sm2_jwt = SM2JWTService()

    def init_db(self):
        """初始化数据库（保留原逻辑）"""
        Base.metadata.create_all(bind=engine)
        logger.info("✅ 数据库表初始化完成")

    def hash_password(self, password):
        """密码哈希（SM3替换原SHA256，逻辑一致）"""
        salt = os.urandom(16).hex()
        hash_value = self.sm3.hash(password, salt)
        return f"{salt}:{hash_value}"

    def verify_password(self, password, hashed_password):
        """验证密码（SM3替换原SHA256，逻辑一致）"""
        try:
            salt, hash_str = hashed_password.split(":", 1)
            return self.sm3.verify_hash(password, hash_str, salt)
        except Exception as e:
            logger.error(f"密码验证失败：{e}")
            return False

    def create_user(self, username, password, phone, role="buyer", email=None):
        """创建用户（保留原逻辑，加密算法替换为SM2/SM3）"""
        try:
            db = next(get_db_session())
            # 检查用户是否已存在
            existing_user = db.query(User).filter(User.username == username).first()
            if existing_user:
                return False, "❌ 用户名已存在"
            # 密码哈希（SM3）
            password_hash = self.hash_password(password)
            # 加密手机号/邮箱（SM2）
            phone_encrypted = self.sm2.encrypt(phone)
            email_encrypted = self.sm2.encrypt(email) if email else None
            # 创建用户
            new_user = User(
                username=username,
                password_hash=password_hash,
                phone=phone,
                phone_encrypted=phone_encrypted,
                email=email,
                email_encrypted=email_encrypted,
                role=role
            )
            db.add(new_user)
            db.commit()
            logger.info(f"✅ 用户 {username} 创建成功")
            return True, "✅ 用户创建成功"
        except Exception as e:
            logger.error(f"创建用户失败：{e}")
            return False, f"❌ 创建用户失败：{str(e)}"

    def user_login(self, username, password):
        """用户登录（保留原逻辑，加密算法替换为SM2/SM3/SM2-JWT）"""
        try:
            db = next(get_db_session())
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return False, "❌ 用户名不存在"
            # 检查账号是否锁定
            if user.is_locked:
                return False, "❌ 账号已被锁定，请联系管理员"
            # 防暴力破解：失败次数超过5次，锁定10分钟
            current_time = time.time()
            if user.fail_count >= 5 and (current_time - user.last_fail_time) < 600:
                return False, "❌ 登录失败次数过多，请10分钟后再试"
            # 重置失败次数超时
            if user.fail_count >= 5 and (current_time - user.last_fail_time) >= 600:
                user.fail_count = 0
                db.commit()
            # 验证密码（SM3）
            if not self.verify_password(password, user.password_hash):
                user.fail_count += 1
                user.last_fail_time = current_time
                db.commit()
                return False, f"❌ 密码错误，剩余尝试次数：{5 - user.fail_count}"
            # 登录成功，重置失败次数
            user.fail_count = 0
            db.commit()
            # 生成SM2-JWT令牌（替换原RS256-JWT）
            tokens = self.sm2_jwt.generate_token(username, user.role)
            return True, tokens
        except Exception as e:
            logger.error(f"用户登录失败：{e}")
            return False, f"❌ 登录失败：{str(e)}"

    def get_user_info(self, username, token):
        """获取用户信息（保留原逻辑，加密算法替换）"""
        # 验证SM2-JWT
        valid, payload = self.sm2_jwt.verify_token(token)
        if not valid:
            return False, payload
        # 验证权限
        if payload["username"] != username and payload["role"] != "admin":
            return False, "❌ 无权限访问该用户信息"
        # 查询用户
        db = next(get_db_session())
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return False, "❌ 用户不存在"
        # 脱敏返回
        phone_desensitized = f"{user.phone[:3]}****{user.phone[-4:]}"
        email_desensitized = None
        if user.email:
            email_parts = user.email.split("@")
            if len(email_parts) == 2:
                email_desensitized = f"{email_parts[0][:2]}****@{email_parts[1]}"
        # 构造返回数据
        user_info = {
            "username": user.username,
            "role": user.role,
            "phone": phone_desensitized,
            "email": email_desensitized,
            "create_time": user.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "is_active": user.is_active
        }
        return True, user_info

    def add_user_address(self, username, token, receiver, phone, province, city, district, detail, is_default=False):
        """添加用户地址（保留原逻辑，加密算法替换为SM2）"""
        # 验证token
        valid, payload = self.sm2_jwt.verify_token(token)
        if not valid:
            return False, payload
        if payload["username"] != username:
            return False, "❌ 无权限添加地址"
        # 加密手机号（SM2）
        phone_encrypted = self.sm2.encrypt(phone)
        # 添加地址
        try:
            db = next(get_db_session())
            # 取消原有默认地址
            if is_default:
                db.query(Address).filter(Address.username == username, Address.is_default == True).update(
                    {Address.is_default: False})
            # 创建新地址
            new_address = Address(
                username=username,
                receiver=receiver,
                phone=phone,
                phone_encrypted=phone_encrypted,
                province=province,
                city=city,
                district=district,
                detail=detail,
                is_default=is_default
            )
            db.add(new_address)
            db.commit()
            return True, "✅ 地址添加成功"
        except Exception as e:
            logger.error(f"添加地址失败：{e}")
            return False, f"❌ 添加地址失败：{str(e)}"

    def create_order(self, username, token, order_items, receiver_info):
        """创建订单（保留原逻辑，加密算法替换为SM2）"""
        # 验证token
        valid, payload = self.sm2_jwt.verify_token(token)
        if not valid:
            return False, payload
        if payload["username"] != username:
            return False, "❌ 无权限创建订单"
        # 生成订单号
        order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
        # 计算总金额
        total_amount = sum(item["quantity"] * item["price"] for item in order_items)
        # 加密收货信息（SM2）
        receiver_phone_encrypted = self.sm2.encrypt(receiver_info["phone"])
        receiver_address = f"{receiver_info['province']}{receiver_info['city']}{receiver_info['district']}{receiver_info['detail']}"
        receiver_address_encrypted = self.sm2.encrypt(receiver_address)
        # 创建订单
        try:
            db = next(get_db_session())
            new_order = Order(
                order_id=order_id,
                username=username,
                total_amount=total_amount,
                status="pending",
                receiver_phone_encrypted=receiver_phone_encrypted,
                receiver_address_encrypted=receiver_address_encrypted
            )
            db.add(new_order)
            # 添加订单项
            for item in order_items:
                order_item = OrderItem(
                    order_id=order_id,
                    product_id=item["product_id"],
                    product_name=item["product_name"],
                    product_price=item["price"],
                    quantity=item["quantity"],
                    subtotal=item["quantity"] * item["price"]
                )
                db.add(order_item)
            db.commit()
            return True, {"order_id": order_id, "total_amount": total_amount}
        except Exception as e:
            logger.error(f"创建订单失败：{e}")
            return False, f"❌ 创建订单失败：{str(e)}"

    def record_payment(self, username, token, order_id, pay_amount, pay_method, sensitive_info=None):
        """记录支付信息（保留原逻辑，加密算法替换为SM2）"""
        # 验证token
        valid, payload = self.sm2_jwt.verify_token(token)
        if not valid:
            return False, payload
        if payload["username"] != username and payload["role"] != "admin":
            return False, "❌ 无权限记录支付信息"
        # 加密敏感信息（SM2）
        card_number_encrypted = None
        alipay_account_encrypted = None
        if pay_method == "card" and sensitive_info:
            card_number_encrypted = self.sm2.encrypt(sensitive_info["card_number"])
        elif pay_method == "alipay" and sensitive_info:
            alipay_account_encrypted = self.sm2.encrypt(sensitive_info["alipay_account"])
        # 记录支付
        try:
            db = next(get_db_session())
            # 更新订单状态
            order = db.query(Order).filter(Order.order_id == order_id).first()
            if not order:
                return False, "❌ 订单不存在"
            order.status = "paid"
            order.pay_time = datetime.now()
            # 创建支付记录
            new_payment = Payment(
                order_id=order_id,
                username=username,
                pay_amount=pay_amount,
                pay_method=pay_method,
                card_number_encrypted=card_number_encrypted,
                alipay_account_encrypted=alipay_account_encrypted,
                transaction_id=sensitive_info.get("transaction_id") if sensitive_info else None
            )
            db.add(new_payment)
            db.commit()
            return True, "✅ 支付记录成功"
        except Exception as e:
            logger.error(f"记录支付失败：{e}")
            return False, f"❌ 记录支付失败：{str(e)}"


# ========== 8. 初始化与测试（保留原逻辑） ==========
if __name__ == "__main__":
    # 初始化服务
    security_service = DataSecurityService()
    security_service.init_db()

    # 测试示例（取消注释可运行）
    # 1. 创建用户
    # success, msg = security_service.create_user("test_user", "Test@123456", "13800138000", "buyer", "test@example.com")
    # print(success, msg)

    # 2. 用户登录
    # success, msg = security_service.user_login("test_user", "Test@123456")
    # if success:
    #     token = msg["access_token"]
    #     print("登录成功，Token：", token)

    # 3. 获取用户信息
    # success, msg = security_service.get_user_info("test_user", token)
    # print(success, msg)

    # 4. 添加地址
    # success, msg = security_service.add_user_address("test_user", token, "张三", "13800138000", "北京市", "北京市", "朝阳区", "测试地址123", True)
    # print(success, msg)

    # 5. 创建订单
    # order_items = [
    #     {"product_id": "P001", "product_name": "测试商品1", "price": 99.9, "quantity": 2},
    #     {"product_id": "P002", "product_name": "测试商品2", "price": 199.9, "quantity": 1}
    # ]
    # receiver_info = {"phone": "13800138000", "province": "北京市", "city": "北京市", "district": "朝阳区", "detail": "测试地址123"}
    # success, msg = security_service.create_order("test_user", token, order_items, receiver_info)
    # print(success, msg)