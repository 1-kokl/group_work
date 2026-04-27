"""主函数：初始化服务并启动多线程运行Flask和命令行菜单"""
import threading
from flask import Flask
from flask_cors import CORS
from app import create_app, db
from app.api import init_api
from app.services.SM2_Utils import SM2Service
from app.services.SM4_Utils import SM4Service
from app.routes import register_blueprints
from app.models.ecommerce_models import Product, Cart, Order, OrderItem

# 使用工厂函数创建应用
app = create_app()

# 配置CORS（允许所有跨域）
CORS(app, resources={r"/api/*": {"origins": "*"}})

# 初始化API文档和蓝图
init_api(app)
register_blueprints(app)


# ========== 初始化国密服务（替换原RSA初始化） ==========
def init_crypto_services():
    print("初始化国密SM2/SM3/SM4加密服务...")
    sm2_service = SM2Service()
    sm4_service = SM4Service()
    print("[OK] 国密加密服务初始化成功")


# ========== 初始化电商数据表（使用SQLAlchemy ORM） ==========
def init_ecommerce_db():
    try:
        db.create_all()
        print("[OK] 电商数据表初始化成功")
    except Exception as e:
        print(f"[WARNING] 电商数据表初始化警告: {e}")


# ========== Flask启动函数 ==========
def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False)


# ========== 命令行菜单（保留原逻辑） ==========
def cli_menu():
    while True:
        print("\n=== 电子商务系统管理菜单 ===")
        print("1. 用户注册")
        print("2. 退出系统")
        choice = input("请选择操作（1/2）：")
        if choice == "1":
            from app.services.register import register
            register()
        elif choice == "2":
            print("再见，系统已退出")
            exit(0)
        else:
            print("[ERROR] 无效选择，请重新输入")


# ========== 主函数 ==========
def main():
    try:
        # 初始化国密加密服务
        init_crypto_services()

        # 初始化数据库表
        print("初始化数据库...")
        init_ecommerce_db()

        # 多线程同时运行Flask服务和命令行菜单
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()

        print("=" * 60)
        print(">> 电子商务系统启动成功!")
        print("=" * 60)

        # 启动命令行菜单
        cli_menu()

    except Exception as e:
        print(f"[ERROR] 系统启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
