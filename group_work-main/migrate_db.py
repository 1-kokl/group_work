"""
数据库迁移脚本 - 添加支付相关字段到 orders 表
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "user.db")


def migrate_orders_table():
    """为 orders 表添加支付相关字段"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(orders)")
        columns = [row[1] for row in cursor.fetchall()]

        # 需要添加的字段
        new_columns = [
            ("payment_status", "TEXT DEFAULT 'unpaid'"),
            ("payment_method", "TEXT"),
            ("transaction_id", "TEXT"),
            ("payment_sign", "TEXT"),
            ("payment_timestamp", "INTEGER")
        ]

        for col_name, col_type in new_columns:
            if col_name not in columns:
                print(f"添加字段: {col_name}")
                cursor.execute(f"ALTER TABLE orders ADD COLUMN {col_name} {col_type}")
            else:
                print(f"字段已存在: {col_name}")

        conn.commit()
        print("✅ 订单表迁移成功")

    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("🔄 开始数据库迁移")
    print("=" * 60)
    migrate_orders_table()
    print("=" * 60)
