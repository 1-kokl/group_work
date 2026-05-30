
import sqlite3
import os
from pathlib import Path

print("=" * 70)
print("证书签发问题诊断")
print("=" * 70)

# 检查1：数据库文件
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user.db')
print(f"\n1️⃣  检查数据库文件:")
if os.path.exists(db_path):
    print(f"   ✅ 数据库存在: {db_path}")
else:
    print(f"   ❌ 数据库不存在: {db_path}")

# 检查2：users 表
if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone():
            print(f"   ✅ users 表存在")
            
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            print(f"   📊 用户数量: {count}")
            
            if count > 0:
                cursor.execute("SELECT username FROM users LIMIT 5")
                users = cursor.fetchall()
                print(f"   👥 用户列表: {', '.join([u[0] for u in users])}")
        else:
            print(f"   ❌ users 表不存在")
        
        # 检查3：certificates 表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='certificates'")
        if cursor.fetchone():
            print(f"   ✅ certificates 表存在")
            
            cursor.execute("SELECT COUNT(*) FROM certificates")
            count = cursor.fetchone()[0]
            print(f"   📊 证书数量: {count}")
        else:
            print(f"   ❌ certificates 表不存在")
            print(f"   💡 运行以下命令创建:")
            print(f"      python create_certificates_table.py")
        
        conn.close()
    except Exception as e:
        print(f"   ❌ 数据库检查失败: {e}")

# 检查4：CA 证书文件
print(f"\n2️⃣  检查 CA 证书文件:")
ca_cert = "certs/rootCA.crt"
ca_key = "certs/rootCA.key"

if os.path.exists(ca_cert):
    print(f"   ✅ CA 证书存在: {ca_cert}")
else:
    print(f"   ❌ CA 证书不存在: {ca_cert}")
    print(f"   💡 运行: python make_ca.py")

if os.path.exists(ca_key):
    print(f"   ✅ CA 私钥存在: {ca_key}")
else:
    print(f"   ❌ CA 私钥不存在: {ca_key}")
    print(f"   💡 运行: python make_ca.py")

# 检查5：当前工作目录
print(f"\n3️⃣  检查工作环境:")
print(f"   📁 当前目录: {os.getcwd()}")
print(f"   📁 项目目录: {os.path.dirname(os.path.abspath(__file__))}")

print("\n" + "=" * 70)
print("诊断完成")
print("=" * 70)
