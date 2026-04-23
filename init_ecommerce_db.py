"""初始化电商相关数据表"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "user.db")


def init_ecommerce_tables():
    """创建电商相关表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 创建商品表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            category TEXT,
            image_url TEXT,
            status BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER
        )
    """)

    # 创建购物车表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS carts (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            selected BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # 创建订单表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            order_no TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            shipping_address TEXT,
            contact_phone TEXT,
            remark TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            paid_at TIMESTAMP
        )
    """)

    # 创建订单项表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            product_name TEXT NOT NULL,
            product_price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    """)

    # 创建索引以提高查询性能
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_carts_user_id ON carts(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id)")

    conn.commit()
    conn.close()
    print("✅ 电商数据表初始化成功")


if __name__ == "__main__":
    init_ecommerce_tables()
