"""
完整数据库迁移脚本 - 确保所有表结构正确
支持 products、carts、orders、order_items 表的创建和字段迁移
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "user.db")


def migrate_database():
    """迁移数据库，添加缺失的字段和表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("=" * 60)
        print("🔄 开始数据库迁移")
        print("=" * 60)
        
        # 1. 检查并创建 products 表
        print("\n📦 1. 检查 products 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                price FLOAT NOT NULL,
                stock INTEGER DEFAULT 0,
                category VARCHAR(100),
                image_url VARCHAR(500),
                status BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER
            )
        """)
        conn.commit()
        print("   ✅ products 表已就绪")
        
        # 2. 检查 products 表的字段
        print("\n🔍 2. 检查 products 表字段...")
        cursor.execute("PRAGMA table_info(products)")
        product_columns = [row[1] for row in cursor.fetchall()]
        print(f"   当前字段: {', '.join(product_columns)}")
        
        # 如果缺少 stock 字段，添加它
        if 'stock' not in product_columns:
            print("   ⚠️  添加缺失的 stock 字段...")
            cursor.execute("ALTER TABLE products ADD COLUMN stock INTEGER DEFAULT 0")
            conn.commit()
            print("   ✅ 已添加 stock 字段")
        
        # 检查其他必要字段
        required_fields = [
            ('category', 'VARCHAR(100)'),
            ('image_url', 'VARCHAR(500)'),
            ('status', 'BOOLEAN DEFAULT 1'),
            ('created_by', 'INTEGER')
        ]
        
        for field_name, field_type in required_fields:
            if field_name not in product_columns:
                print(f"   ⚠️  添加缺失的 {field_name} 字段...")
                cursor.execute(f"ALTER TABLE products ADD COLUMN {field_name} {field_type}")
                conn.commit()
                print(f"   ✅ 已添加 {field_name} 字段")
        
        # 3. 检查并创建 carts 表
        print("\n🛒 3. 检查 carts 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS carts (
                id VARCHAR(36) PRIMARY KEY,
                user_id INTEGER NOT NULL,
                product_id VARCHAR(36) NOT NULL,
                quantity INTEGER DEFAULT 1,
                selected BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        conn.commit()
        print("   ✅ carts 表已就绪")
        
        # 4. 检查并创建 orders 表
        print("\n📋 4. 检查 orders 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id VARCHAR(36) PRIMARY KEY,
                order_no VARCHAR(64) UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                total_amount FLOAT NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                shipping_address TEXT,
                contact_phone VARCHAR(20),
                remark TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                paid_at DATETIME,
                payment_status VARCHAR(20) DEFAULT 'unpaid',
                payment_method VARCHAR(50),
                transaction_id VARCHAR(100),
                payment_sign TEXT,
                payment_timestamp INTEGER
            )
        """)
        conn.commit()
        print("   ✅ orders 表已就绪")
        
        # 检查 orders 表的支付字段
        cursor.execute("PRAGMA table_info(orders)")
        order_columns = [row[1] for row in cursor.fetchall()]
        
        payment_fields = [
            ('payment_status', "VARCHAR(20) DEFAULT 'unpaid'"),
            ('payment_method', 'VARCHAR(50)'),
            ('transaction_id', 'VARCHAR(100)'),
            ('payment_sign', 'TEXT'),
            ('payment_timestamp', 'INTEGER')
        ]
        
        for field_name, field_type in payment_fields:
            if field_name not in order_columns:
                print(f"   ⚠️  添加缺失的 {field_name} 字段...")
                cursor.execute(f"ALTER TABLE orders ADD COLUMN {field_name} {field_type}")
                conn.commit()
                print(f"   ✅ 已添加 {field_name} 字段")
        
        # 5. 检查并创建 order_items 表
        print("\n📝 5. 检查 order_items 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id VARCHAR(36) PRIMARY KEY,
                order_id VARCHAR(36) NOT NULL,
                product_id VARCHAR(36) NOT NULL,
                product_name VARCHAR(200) NOT NULL,
                product_price FLOAT NOT NULL,
                quantity INTEGER NOT NULL,
                subtotal FLOAT NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        conn.commit()
        print("   ✅ order_items 表已就绪")
        
        print("\n" + "=" * 60)
        print("✅ 数据库迁移完成！")
        print("=" * 60)
        
        # 显示当前表结构
        print("\n📊 当前数据库表:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"   - {table[0]}: {count} 条记录")
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()


def migrate_orders_table():
    """兼容旧版本的订单表迁移函数（已合并到 migrate_database）"""
    print("⚠️  此函数已废弃，请使用 migrate_database()")
    migrate_database()


if __name__ == "__main__":
    migrate_database()
