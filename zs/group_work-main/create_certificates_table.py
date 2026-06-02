
import sqlite3
import os

# 使用项目根目录的 user.db
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user.db')

def create_certificates_table():
    """创建 certificates 表"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查表是否已存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='certificates'")
        if cursor.fetchone():
            print("✅ certificates 表已存在，无需创建")
            conn.close()
            return True
        
        # 创建 certificates 表
        cursor.execute('''
        CREATE TABLE certificates (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            fingerprint TEXT UNIQUE NOT NULL,
            serial_number TEXT NOT NULL,
            subject TEXT NOT NULL,
            cert_type TEXT NOT NULL DEFAULT 'client',
            status INTEGER NOT NULL DEFAULT 1,
            issued_at TEXT NOT NULL,
            expired_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        ''')
        
        # 创建索引以加速查询
        cursor.execute('CREATE INDEX idx_cert_fingerprint ON certificates(fingerprint)')
        cursor.execute('CREATE INDEX idx_cert_user_id ON certificates(user_id)')
        cursor.execute('CREATE INDEX idx_cert_status ON certificates(status)')
        
        conn.commit()
        conn.close()
        
        print(f"✅ certificates 表创建成功: {DB_PATH}")
        print("✅ 表结构: id, user_id, fingerprint, serial_number, subject, cert_type, status, issued_at, expired_at")
        print("✅ 已创建索引: fingerprint, user_id, status")
        
        return True
        
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    create_certificates_table()
