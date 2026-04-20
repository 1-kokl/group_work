import sqlite3
import os

# 获取数据库路径
ROOT = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(ROOT, "user.db")

def migrate_database():
    """添加 role 字段到 users 表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查表是否存在
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='users'
    """)
    
    if not cursor.fetchone():
        print("❌ users 表不存在，请先运行 create_table.py")
        conn.close()
        return False
    
    # 检查 role 字段是否已存在
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'role' not in columns:
        try:
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN role TEXT NOT NULL DEFAULT 'user'
            """)
            conn.commit()
            print("✅ 成功添加 role 字段")
        except Exception as e:
            print(f"❌ 添加 role 字段失败: {e}")
            conn.close()
            return False
    else:
        print("ℹ️  role 字段已存在")
    
    conn.close()
    return True

if __name__ == "__main__":
    print(f"📁 数据库路径: {DB_PATH}")
    if migrate_database():
        print("✅ 数据库迁移完成")
    else:
        print("❌ 数据库迁移失败")
