import threading
import time
from flask_new import app, run_flask, cli_menu, init_db, rsa_service, jwt_service

def main():
    """主函数：初始化服务并启动多线程运行Flask和命令行菜单"""
    try:
        # 初始化RSA服务
        print("初始化RSA加密服务...")
        rsa_service.load_keys()
        
        # 初始化JWT服务
        print("初始化JWT认证服务...")
        global jwt_service
        jwt_service = jwt_service
        
        # 初始化数据库
        print("初始化数据库...")
        with app.app_context():
            init_db()
        
        # 启动Flask服务线程
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        print("Flask服务已启动，运行在 http://0.0.0.0:5000")
        time.sleep(1)  # 等待Flask服务启动
        
        # 启动命令行交互菜单
        print("\n进入命令行交互模式")
        cli_menu()
        
    except Exception as e:
        print(f"启动失败：{str(e)}")

if __name__ == "__main__":
    main()
