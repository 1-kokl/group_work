import sqlite3
import os
from .SM3_Service import hash_password
from .SM4_Utils import SM4Service

# ========== 初始化数据库连接 ==========
conn = sqlite3.connect('user.db')
cursor = conn.cursor()

# 确保表结构存在（新增phone_encrypted字段）
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    phone TEXT NOT NULL,
    phone_encrypted TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user'
)
''')
conn.commit()

# ========== 输入校验函数（保留原逻辑） ==========
def check_username(username):
    if len(username) < 4 or len(username) > 20:
        return False, "用户名长度需4-20位"
    if not username.isalnum():
        return False, "用户名仅支持字母和数字"
    return True, ""

def check_password_strength(password):
    if len(password) < 8:
        return False, "密码长度至少8位"
    if not any(c.isupper() for c in password):
        return False, "密码需包含大写字母"
    if not any(c.isdigit() for c in password):
        return False, "密码需包含数字"
    return True, ""

def check_phone(phone):
    if len(phone) != 11 or not phone.isdigit():
        return False, "手机号格式错误（11位数字）"
    return True, ""

# ========== 本地文档写入函数（保留原逻辑） ==========
def write_to_doc(user_info):
    with open("user_registry.txt", "a", encoding="utf-8") as f:
        f.write(f"{user_info}\n")
    print("✅ 用户信息已写入本地文档")

def sync_to_github():
    print("🔄 提示：请手动同步user_registry.txt到GitHub仓库")

# ========== 注册核心函数（替换RSA为SM4/SM3） ==========
def register():
    print("=== 用户注册 ===")
    username = input("请输入用户名：")
    username_valid, username_msg = check_username(username)
    if not username_valid:
        print(username_msg)
        return

    password = input("请输入密码：")
    pwd_valid, pwd_msg = check_password_strength(password)
    if not pwd_valid:
        print(pwd_msg)
        return
    password_hash = hash_password(password)  # SM3哈希

    phone = input("请输入手机号：")
    phone_valid, phone_msg = check_phone(phone)
    if not phone_valid:
        print(phone_msg)
        return

    # 初始化SM4服务并加密手机号（替代RSA）
    sm4_service = SM4Service()
    try:
        encrypted_phone = sm4_service.encrypt(phone)
        print("✅ 敏感信息加密完成")
        print(f"加密手机号: {encrypted_phone[:30]}...")
    except Exception as e:
        print(f"❌ 加密失败: {e}")
        return

    # 1. 写入SQLite数据库
    try:
        cursor.execute('''
                INSERT INTO users (username, password_hash, phone, phone_encrypted, role)
                VALUES (?, ?, ?, ?, ?)
                ''', (username, password_hash, phone, encrypted_phone, 'user'))
        conn.commit()
        print("✅ 注册成功！加密数据已写入SQLite数据库")
    except sqlite3.IntegrityError:
        print("❌ 用户名已存在")
        return

    # 2. 写入本地文档
    user_info = {
        "username": username,
        "pwd_hash": password_hash,
        "phone_encrypted": encrypted_phone,
    }
    write_to_doc(user_info)

    # 3. 提示GitHub同步
    sync_to_github()

# ========== 敏感文件列表（新增国密密钥） ==========
SENSITIVE_FILES = [
    "sm2_key.txt",
    "sm4_key.txt",
    "user_registry.txt",
    "user.db"
]

if __name__ == "__main__":
    register()