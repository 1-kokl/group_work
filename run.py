"""主函数：初始化服务并启动多线程运行Flask和命令行菜单"""
import threading
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from flask import Flask
from flask_cors import CORS
from app.api._init_ import init_api
from app.services.SM2_Utils import SM2Service
from app.services.SM4_Utils import SM4Service

# ========== 初始化数据库 ==========
engine = create_engine('sqlite:///user.db')
Base = declarative_base()

# ========== 初始化Flask应用 ==========
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
init_api(app)

# ========== 初始化国密服务（替换原RSA初始化） ==========
def init_crypto_services():
    print("初始化国密SM2/SM3/SM4加密服务...")
    # 预加载SM2/SM4密钥（首次运行自动生成）
    sm2_service = SM2Service()
    sm4_service = SM4Service()
    print("✅ 国密加密服务初始化成功")

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
            print("👋 系统已退出")
            exit(0)
        else:
            print("❌ 无效选择，请重新输入")

# ========== 主函数 ==========
def main():
    try:
        # 初始化国密加密服务
        init_crypto_services()

        # 初始化数据库表
        print("初始化数据库...")
        Base.metadata.create_all(bind=engine)

        # 多线程同时运行Flask服务和命令行菜单
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()

        print("=" * 60)
        print("🚀 电子商务系统启动成功!")
        print("=" * 60)

        # 启动命令行菜单
        cli_menu()

    except Exception as e:
        print(f"❌ 系统启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()