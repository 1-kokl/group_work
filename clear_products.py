"""清空所有商品数据"""
import sqlite3
import os

def clear_all_products():
    """清空商品表"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'user.db')
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("⚠️  即将清空以下数据表：")
        print("   - products（商品表）")
        print("   - carts（购物车表）")
        print("   - order_items（订单项表）")
        print("   - orders（订单表）")
        print()
        
        confirm = input("确认清空？(yes/no): ").strip().lower()
        
        if confirm != 'yes':
            print("❌ 操作已取消")
            return
        
        cursor.execute("DELETE FROM products")
        cursor.execute("DELETE FROM carts")
        cursor.execute("DELETE FROM order_items")
        cursor.execute("DELETE FROM orders")
        
        conn.commit()
        conn.close()
        
        print("✅ 所有商品数据已清空！")
        
    except Exception as e:
        print(f" 清空失败: {e}")

if __name__ == "__main__":
    clear_all_products()
