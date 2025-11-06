from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import logging
from datetime import datetime, timedelta
import jwt as pyjwt
from Crypto.PublicKey import RSA
from Crypto.Util.number import bytes_to_long, long_to_bytes
import base64
import json
import random
import re
import hashlib
import time
import string
import os
import threading  # 新增：用于多线程同时运行Flask和命令行菜单

# ========== 1. Flask应用初始化 ==========
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config["JWT_ALGORITHM"] = "RS256"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=2)
jwt = JWTManager(app)

# ========== 2. 数据库配置 ==========
engine = create_engine(
    "sqlite:///ecommerce.db",
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    echo=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ========== 3. RSA加密工具类 ==========
class RSAServices:
    def __init__(self):
        self.private_key = None
        self.public_key = None

    @staticmethod
    def serialize(info):
        if isinstance(info, (list, dict)):
            json_str = json.dumps(info)
            return base64.b64encode(json_str.encode()).decode()

    @staticmethod
    def deserialize(serialize_data):
        try:
            json_str = base64.b64decode(serialize_data.encode())
            return json.loads(json_str.decode("utf-8"))
        except Exception as e:
            app.logger.error(f"反序列化失败：{e}")
            raise

    @staticmethod
    def is_prime(n):
        if n % 2 == 0:
            return False
        d = n - 1
        s = 0
        while d % 2 == 0:
            s += 1
            d //= 2
        a = 2
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            return True
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                return True
        return False

    @staticmethod
    def get_prime(bits):
        while True:
            p = random.getrandbits(bits)
            p |= (1 << (bits - 1)) | 1
            if RSAServices.is_prime(p):
                return p

    @staticmethod
    def gra_pra_pub_key(e=65537):
        p = RSAServices.get_prime(1024)
        q = RSAServices.get_prime(1024)
        n = p * q
        phi_n = (p - 1) * (q - 1)
        d = pow(e, -1, phi_n)
        private_key = {"type": "private", "n": n, "d": d, "e": e, "key_size": 1024}
        public_key = {"type": "public", "n": n, "e": e, "key_size": 1024}
        return private_key, public_key

    def load_keys(self, e=65537):
        try:
            with open("private_key.txt", "r", encoding="utf-8") as f:
                self.private_key = self.deserialize(f.read())
            with open("public_key.txt", "r", encoding="utf-8") as f:
                self.public_key = self.deserialize(f.read())
            app.logger.info("✅ 密钥对加载成功")
        except Exception as e:
            app.logger.error(f"❌ 密钥加载失败：{e}，将生成新密钥")
            self.generate_keys()

    def generate_keys(self):
        self.private_key, self.public_key = self.gra_pra_pub_key(65537)
        with open("private_key.txt", "w", encoding="utf-8") as f:
            f.write(self.serialize(self.private_key))
        with open("public_key.txt", "w", encoding="utf-8") as f:
            f.write(self.serialize(self.public_key))
        app.logger.info("✅ 新密钥对已生成并保存")

    def encrypt(self, info):
        if self.public_key is None:
            raise RuntimeError("❌ 公钥未初始化，无法加密")
        if not isinstance(info, str):
            info = str(info)
        m = bytes_to_long(info.encode('utf-8'))
        n = self.public_key['n']
        e = self.public_key['e']
        max_length = (self.public_key['key_size'] // 8) - 11
        if len(info.encode('utf-8')) > max_length:
            raise ValueError(f"❌ 数据过长，最大支持{max_length}字节")
        c = pow(m, e, n)
        encrypted_bytes = long_to_bytes(c)
        return base64.b64encode(encrypted_bytes).decode('utf-8')

    def decrypt(self, encrypted_data):
        if self.private_key is None:
            raise RuntimeError("❌ 私钥未初始化，无法解密")
        encrypted_bytes = base64.b64decode(encrypted_data)
        c = bytes_to_long(encrypted_bytes)
        n = self.private_key['n']
        d = self.private_key['d']
        m = pow(c, d, n)
        decrypted_bytes = long_to_bytes(m)
        return decrypted_bytes.decode('utf-8')

rsa_service = RSAServices()
rsa_service.load_keys()

# ========== 4. JWT工具类 ==========
class JWTService:
    def __init__(self):
        self.rsa = rsa_service
        self.algorithm = "RS256"
        self.pem_private_key = self._dict_to_pem_private()
        self.pem_public_key = self._dict_to_pem_public()
        jwt.user_lookup_loader(self._load_user)

    def _dict_to_pem_private(self):
        try:
            n = self.rsa.private_key["n"]
            e = self.rsa.private_key["e"]
            d = self.rsa.private_key["d"]
            key = RSA.construct((n, e, d))
            return key.export_key().decode('utf-8')
        except Exception as e:
            raise ValueError(f"❌ 私钥格式转换失败：{e}")

    def _dict_to_pem_public(self):
        try:
            n = self.rsa.public_key["n"]
            e = self.rsa.public_key["e"]
            key = RSA.construct((n, e))
            return key.export_key().decode('utf-8')
        except Exception as e:
            raise ValueError(f"❌ 公钥格式转换失败：{e}")

    def generate_token(self, username, role):
        access_exp = datetime.utcnow() + timedelta(hours=2)
        access_payload = {"username": username, "role": role, "exp": access_exp, "type": "access"}
        access_token = pyjwt.encode(access_payload, self.pem_private_key, algorithm=self.algorithm)
        refresh_exp = datetime.utcnow() + timedelta(days=7)
        refresh_payload = {"username": username, "exp": refresh_exp, "type": "refresh"}
        refresh_token = pyjwt.encode(refresh_payload, self.pem_private_key, algorithm=self.algorithm)
        return {"access_token": access_token, "refresh_token": refresh_token}

    def verify_token(self, token):
        try:
            payload = pyjwt.decode(token, self.pem_public_key, algorithms=[self.algorithm])
            if payload["type"] != "access":
                return False, "❌ 仅支持access令牌"
            return True, payload
        except pyjwt.ExpiredSignatureError:
            return False, "❌ Token已过期"
        except Exception as e:
            return False, f"❌ Token验证失败：{str(e)}"

    def _load_user(self, _jwt_header, jwt_data):
        username = jwt_data["sub"]
        return DAO().get_user_by_username(username)

jwt_service = JWTService()

# ========== 5. 数据模型 ==========
class User(Base):
    __tablename__ = "users"
    username = Column(String(50), primary_key=True)
    password_hash = Column(String(100), nullable=False)
    fail_count = Column(Integer, default=0)
    last_fail_time = Column(Float, default=0)
    role = Column(String(20), nullable=False, default="buyer")
    phone = Column(String(20), nullable=False)
    phone_encrypted = Column(String(200), nullable=False)
    addresses = relationship("Address", back_populates="user")
    cart = relationship("Cart", uselist=False, back_populates="user")
    orders = relationship("Order", back_populates="user")
    evaluations = relationship("Evaluation", back_populates="user")
    purchases = relationship("Purchase", back_populates="user")

class Address(Base):
    __tablename__ = "addresses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    recipient = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=False)
    detail = Column(String(200), nullable=False)
    username = Column(String(50), ForeignKey("users.username"), nullable=False)
    user = relationship("User", back_populates="addresses")

class CommodityCategory(Base):
    __tablename__ = "commodity_categories"
    category_id = Column(Integer, primary_key=True, autoincrement=True)
    category_name = Column(String(50), nullable=False)
    parent_id = Column(Integer, default=0)
    commodities = relationship("Commodity", back_populates="category")

class Manufacturer(Base):
    __tablename__ = "manufacturers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    address = Column(String(200))
    phone = Column(String(20))
    commodities = relationship("Commodity", back_populates="manufacturer")

class Commodity(Base):
    __tablename__ = "commodities"
    name = Column(String(100), primary_key=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    status = Column(Boolean, nullable=False, default=True)
    category_id = Column(Integer, ForeignKey("commodity_categories.category_id"), nullable=False)
    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"), nullable=False)
    category = relationship("CommodityCategory", back_populates="commodities")
    manufacturer = relationship("Manufacturer", back_populates="commodities")
    cart_items = relationship("CartItem", back_populates="commodity")
    order_items = relationship("OrderItem", back_populates="commodity")
    evaluations = relationship("Evaluation", back_populates="commodity")
    purchases = relationship("Purchase", back_populates="commodity")

class Cart(Base):
    __tablename__ = "carts"
    username = Column(String(50), ForeignKey("users.username"), primary_key=True)
    create_time = Column(DateTime, default=datetime.now)
    item_count = Column(Integer, default=0)
    user = relationship("User", back_populates="cart")
    items = relationship("CartItem", back_populates="cart")

class CartItem(Base):
    __tablename__ = "cart_items"
    cart_username = Column(String(50), ForeignKey("carts.username"), primary_key=True)
    commodity_name = Column(String(100), ForeignKey("commodities.name"), primary_key=True)
    quantity = Column(Integer, nullable=False, default=1)
    selected = Column(Boolean, default=True)
    cart = relationship("Cart", back_populates="items")
    commodity = relationship("Commodity", back_populates="cart_items")

class Order(Base):
    __tablename__ = "orders"
    order_number = Column(String(50), primary_key=True)
    total_amount = Column(Float, nullable=False)
    create_time = Column(DateTime, default=datetime.now)
    status = Column(String(20), default="待支付")
    username = Column(String(50), ForeignKey("users.username"), nullable=False)
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    evaluations = relationship("Evaluation", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    order_number = Column(String(50), ForeignKey("orders.order_number"), primary_key=True)
    commodity_name = Column(String(100), ForeignKey("commodities.name"), primary_key=True)
    quantity = Column(Integer, nullable=False)
    price_at_purchase = Column(Float, nullable=False)
    order = relationship("Order", back_populates="items")
    commodity = relationship("Commodity", back_populates="order_items")

class Evaluation(Base):
    __tablename__ = "evaluations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    score = Column(Integer, nullable=False)
    content = Column(Text)
    time = Column(DateTime, default=datetime.now)
    username = Column(String(50), ForeignKey("users.username"), nullable=False)
    order_number = Column(String(50), ForeignKey("orders.order_number"), nullable=False)
    commodity_name = Column(String(100), ForeignKey("commodities.name"), nullable=False)
    user = relationship("User", back_populates="evaluations")
    order = relationship("Order", back_populates="evaluations")
    commodity = relationship("Commodity", back_populates="evaluations")

class Purchase(Base):
    __tablename__ = "purchases"
    username = Column(String(50), ForeignKey("users.username"), primary_key=True)
    commodity_name = Column(String(100), ForeignKey("commodities.name"), primary_key=True)
    purchase_time = Column(DateTime, default=datetime.now, primary_key=True)
    user = relationship("User", back_populates="purchases")
    commodity = relationship("Commodity", back_populates="purchases")

# ========== 6. DAO数据访问层 ==========
class DAO:
    def __init__(self):
        self.db = SessionLocal()

    def __del__(self):
        self.db.close()

    def _audit_log(self, action, detail):
        app.logger.info(f"Action: {action}, Detail: {detail}")

    def get_user_by_username(self, username):
        user = self.db.query(User).filter(User.username == username).first()
        self._audit_log("QUERY_USER", f"Username: {username}")
        return user

    def create_user(self, user_info):
        new_user = User(
            username=user_info["username"],
            password_hash=user_info["pwd_hash"],
            phone=user_info["phone"],
            phone_encrypted=user_info["phone_encrypted"],
            role=user_info.get("role", "buyer")
        )
        self.db.add(new_user)
        self.db.commit()
        self._audit_log("CREATE_USER", f"Username: {user_info['username']}")
        return new_user

    def update_user_fail_count(self, username, fail_count, last_fail_time):
        user = self.get_user_by_username(username)
        if user:
            user.fail_count = fail_count
            user.last_fail_time = last_fail_time
            self.db.commit()
            self._audit_log("UPDATE_USER_FAIL_COUNT", f"Username: {username}, Fail Count: {fail_count}")
            return True
        return False

# ========== 7. 业务工具函数 ==========
LOCAL_DOC = "user_registry.txt"
SENSITIVE_FILES = [LOCAL_DOC, "private_key.txt", "public_key.txt"]

def ensure_gitignore():
    gitignore_path = ".gitignore"
    existing_content = ""
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            existing_content = f.read()
    with open(gitignore_path, "a", encoding="utf-8") as f:
        for file in SENSITIVE_FILES:
            if file not in existing_content:
                f.write(f"\n# 敏感文件（自动添加）\n{file}")
    app.logger.info(f"✅ .gitignore已配置敏感文件：{SENSITIVE_FILES}")

def check_username(username):
    if not 6 <= len(username) <= 20:
        return False, "❌ 用户名长度需在6-20位之间"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "❌ 用户名仅支持字母、数字、下划线"
    return True, "✅ 用户名合法"

def register_service(user_data):
    username = user_data.get("username")
    password = user_data.get("password")
    phone = user_data.get("phone")

    username_valid, username_msg = check_username(username)
    if not username_valid:
        return {"code": 400, "msg": username_msg}
    if len(password) < 8 or not (any(c.isupper() for c in password) and any(c.islower() for c in password) and any(c.isdigit() for c in password) and any(c in "!@#$%^&*()" for c in password)):
        return {"code": 400, "msg": "❌ 密码需8位以上，含大小写、数字、特殊字符"}
    if not re.match(r'^1[3-9]\d{9}$', phone):
        return {"code": 400, "msg": "❌ 手机号需为13-19开头的11位数字"}

    dao = DAO()
    if dao.get_user_by_username(username):
        return {"code": 400, "msg": "❌ 用户名已存在"}

    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    try:
        encrypted_phone = rsa_service.encrypt(phone)
    except Exception as e:
        return {"code": 500, "msg": f"❌ 手机号加密失败：{str(e)}"}

    user_info = {
        "username": username,
        "pwd_hash": password_hash,
        "phone": phone,
        "phone_encrypted": encrypted_phone
    }
    dao.create_user(user_info)
    with open(LOCAL_DOC, "a", encoding="utf-8") as f:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        f.write(f"{timestamp}|{username}|{password_hash}|{encrypted_phone}\n")
    app.logger.info(f"✅ 用户{username}注册成功")
    return {"code": 200, "msg": "✅ 注册成功"}

def login_service(user_data):
    username = user_data.get("username")
    password = user_data.get("password")
    dao = DAO()
    user = dao.get_user_by_username(username)

    if not user:
        return {"code": 401, "msg": "❌ 用户名不存在"}
    if not password:
        return {"code": 400, "msg": "❌ 密码不能为空"}

    if user.fail_count >= 5:
        lock_remaining = 3600 - (time.time() - user.last_fail_time)
        if lock_remaining > 0:
            return {"code": 403, "msg": f"❌ 账户锁定，剩余{int(lock_remaining)}秒"}
        else:
            dao.update_user_fail_count(username, 0, 0)

    input_password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    if input_password_hash != user.password_hash:
        new_fail_count = user.fail_count + 1
        dao.update_user_fail_count(username, new_fail_count, time.time())
        return {"code": 401, "msg": f"❌ 密码错误，剩余{5 - new_fail_count}次尝试"}

    tokens = jwt_service.generate_token(username, user.role)
    dao.update_user_fail_count(username, 0, 0)
    return {
        "code": 200,
        "msg": "✅ 登录成功",
        "data": {"access_token": tokens["access_token"], "role": user.role}
    }

# ========== 8. 命令行交互菜单（恢复图一功能） ==========
def cli_menu():
    """恢复原代码的命令行交互菜单"""
    print("=== 电子商务系统用户管理 ===")
    while True:
        print("1. 用户注册（自动加密敏感信息+本地备份）")
        print("2. 用户登录（生成JWT令牌+角色权限展示）")
        print("3. 退出系统")
        choice = input("请选择操作（1/2/3）：")
        
        if choice == "1":
            # 用户注册（终端输入）
            username = input("请输入用户名：")
            password = input("请输入密码：")
            phone = input("请输入手机号：")
            user_data = {"username": username, "password": password, "phone": phone}
            result = register_service(user_data)
            print(result["msg"])
        
        elif choice == "2":
            # 用户登录（终端输入）
            username = input("请输入用户名：")
            password = input("请输入密码：")
            user_data = {"username": username, "password": password}
            result = login_service(user_data)
            print(result["msg"])
            if result["code"] == 200:
                print(f"JWT令牌：{result['data']['access_token']}")
                print(f"用户角色：{result['data']['role']}")
        
        elif choice == "3":
            print("退出系统")
            break
        
        else:
            print("❌ 无效选项，请重新选择")

# ========== 9. Flask接口 ==========
@app.route("/api/v1/user/register", methods=["POST"])
def user_register():
    user_data = request.get_json()
    result = register_service(user_data)
    return jsonify(result), result["code"]

@app.route("/api/v1/user/login", methods=["POST"])
def user_login():
    user_data = request.get_json()
    result = login_service(user_data)
    return jsonify(result), result["code"]

@app.route("/api/v1/user/info", methods=["GET"])
@jwt_required()
def get_user_info():
    username = get_jwt_identity()
    user = DAO().get_user_by_username(username)
    if not user:
        return jsonify({"code": 404, "msg": "❌ 用户不存在"}), 404
    return jsonify({
        "code": 200,
        "msg": "✅ 获取成功",
        "data": {
            "username": user.username,
            "role": user.role,
            "phone": user.phone[:3] + "****" + user.phone[-4:]
        }
    }), 200

@app.route("/api/v1/db/init", methods=["GET"])
def init_db():
    Base.metadata.create_all(bind=engine)
    app.logger.info("✅ 数据库初始化完成")
    return jsonify({"code": 200, "msg": "✅ 数据库初始化成功"}), 200

# ========== 10. 启动Flask服务+命令行菜单（多线程） ==========
def run_flask():
    app.run(host="0.0.0.0", port=5000, debug=False)  # 注意：debug=True会影响多线程

if __name__ == "__main__":
    ensure_gitignore()
    # 初始化数据库（首次运行需执行）
    Base.metadata.create_all(bind=engine)
    
    # 多线程同时运行Flask服务和命令行菜单
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True  # 主程序退出时，Flask线程自动结束
    flask_thread.start()
    
    # 启动命令行菜单（图一效果）
    cli_menu()
