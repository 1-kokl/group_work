"""简化版启动脚本 - 只运行 Flask 服务"""
from app import create_app
from flask_cors import CORS

# 使用应用工厂创建应用（已经包含了所有蓝图注册）
app = create_app()

# 启用 CORS - 更宽松的配置
CORS(app, 
     resources={r"/api/*": {"origins": "*"}},
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
)

# 添加全局 OPTIONS 处理，确保 CORS 头正确设置
@app.after_request
def after_request(response):
    """确保所有响应都包含 CORS 头"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS,PATCH')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 正在启动 Flask 服务...")
    print("=" * 60)
    print("📍 服务地址: http://localhost:5000")
    print("📚 API文档: http://localhost:5000/docs/")
    print("✅ CORS 已启用")
    print("=" * 60)
    
    # 直接运行 Flask（不使用多线程）
    app.run(host='0.0.0.0', port=5000, debug=True)
