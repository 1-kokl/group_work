"""
快速创建测试用户用于支付流程测试
"""
import sqlite3
from app.services.SM3_Service import hash_password
from app.services.SM4_Utils import SM4Service

def create_test_user():
    """创建测试用户"""
    username = "testuser"
    password = "TestPass123!"
    phone = "13800138000"
    
    print("=" * 60)
    print("🔧 创建测试用户")
    print("=" * 60)
    
    # 初始化SM4加密
    sm4_service = SM4Service()
    encrypted_phone = sm4_service.encrypt(phone)
    
    # 哈希密码
    password_hash = hash_password(password)
    
    # 连接数据库
    conn = sqlite3.connect('user.db')
    cursor = conn.cursor()
    
    try:
        # 检查用户是否已存在
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        existing = cursor.fetchone()
        
        if existing:
            print(f"⚠️ 用户 {username} 已存在")
            print(f"   尝试使用密码: {password}")
            return
        
        # 插入新用户
        cursor.execute('''
            INSERT INTO users (username, password_hash, phone, phone_encrypted, role)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, password_hash, phone, encrypted_phone, 'user'))
        
        conn.commit()
        print(f"✅ 测试用户创建成功！")
        print(f"   用户名: {username}")
        print(f"   密码: {password}")
        print(f"   手机号: {phone}")
        print(f"   角色: user")
        
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    print("=" * 60)

if __name__ == "__main__":
    create_test_user()