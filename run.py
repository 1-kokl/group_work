import threading
import time
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
try:
    # 尝试从flask_new导入必要的组件
    from flask_new import app, cli_menu, rsa_service, jwt_service, Base, engine
    from flask_new import CORS

    print("✅ 成功导入flask_new模块")
except ImportError as e:
    print(f"❌ 导入flask_new失败: {e}")
    # 尝试直接导入必要的组件
    try:
        from flask import Flask
        from flask_cors import CORS

        print("✅ 使用直接导入方式")
        # 在这里创建app实例或其他必要的组件
    except ImportError as e2:
        print(f"❌ 直接导入也失败: {e2}")
        exit(1)


def run_flask():
    """运行Flask应用"""
    try:
        app.run(host="0.0.0.0", port=5000, debug=False)
    except Exception as e:
        print(f"❌ Flask启动失败: {e}")


def main():
    """主函数：初始化服务并启动多线程运行Flask和命令行菜单"""
    try:
        # 初始化RSA服务
        print("初始化RSA加密服务...")
        rsa_service.load_keys()

        # 初始化数据库
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