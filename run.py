import threading
import time
from flask_new import app, run_flask, cli_menu, rsa_service, jwt_service, Base, engine
from flask_new import SecurityMiddleware, create_swagger_spec, swagger_ui_blueprint
from flask_cors import CORS
import os


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
            Base.metadata.create_all(bind=engine)
            print("数据库初始化完成")

        # 初始化安全中间件
        print("初始化安全中间件...")
        security_middleware = SecurityMiddleware(app)
        print("安全中间件初始化完成")

        # 生成Swagger文档
        print("生成Swagger API文档...")
        create_swagger_spec()
        app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)
        print("Swagger文档生成完成")

        # 创建静态文件目录
        os.makedirs('static', exist_ok=True)

        # 启动Flask服务线程
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        print("Flask服务已启动，运行在 http://0.0.0.0:5000")
        print(f"API文档地址: http://localhost:5000{SWAGGER_URL}")
        time.sleep(1)

        # 启动命令行交互菜单
        print("\n进入命令行交互模式")
        cli_menu()

    except Exception as e:
        print(f"启动失败：{str(e)}")


if __name__ == "__main__":
    # 可以选择运行测试
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        from test_api import run_tests_with_report

        success = run_tests_with_report()
        sys.exit(0 if success else 1)
    else:
        main()