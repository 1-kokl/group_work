from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
import sqlite3  # 替换pymysql为sqlite3
import re
from datetime import timedelta

# 初始化Flask应用
app = Flask(__name__)
# 配置CORS（开发环境允许所有跨域）
CORS(app, resources={r"/api/*": {"origins": "*"}})
# JWT密钥（生产环境需改为复杂随机字符串）
app.config["JWT_SECRET_KEY"] = "your-super-secret-key"
# JWT过期时间（1小时）
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
jwt = JWTManager(app)

# -------------------------- 替换：SQLite数据库连接 --------------------------
def get_db_connection():
    # 连接SQLite数据库（文件为user.db，不存在则自动创建）
    conn = sqlite3.connect('user.db')
    # 设置游标返回字典格式（更易操作）
    conn.row_factory = sqlite3.Row
    return conn


# -------------------------- 用户注册接口（仅数据库操作适配SQLite） --------------------------
@app.route("/api/v1/user/register", methods=["POST"])
def user_register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    # 1. 参数校验（无变化）
    if not username or not password:
        return jsonify({"code": 400, "msg": "用户名/密码不能为空"}), 400
    if len(username) < 2 or len(username) > 20:
        return jsonify({"code": 400, "msg": "用户名长度必须在2-20之间"}), 400
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return jsonify({"code": 400, "msg": "用户名仅支持字母、数字、下划线"}), 400

    # 2. SQLite数据库操作（语法略有调整）
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 检查用户名是否已存在
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return jsonify({"code": 400, "msg": "用户名已存在"}), 400
        
        # 插入新用户
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        conn.commit()
        return jsonify({"code": 200, "msg": "注册成功"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"code": 500, "msg": f"服务器错误: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


# -------------------------- 用户登录接口（仅数据库操作适配SQLite） --------------------------
@app.route("/api/v1/user/login", methods=["POST"])
def user_login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    # 1. 参数校验（无变化）
    if not username or not password:
        return jsonify({"code": 400, "msg": "用户名/密码不能为空"}), 400

    # 2. SQLite数据库验证
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password)
        )
        user = cursor.fetchone()
        if not user:
            return jsonify({"code": 401, "msg": "用户名或密码错误"}), 401
        
        # 生成JWT Token（无变化）
        access_token = create_access_token(identity=username)
        return jsonify({
            "code": 200,
            "msg": "登录成功",
            "data": {"token": access_token}
        }), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": f"服务器错误: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


# -------------------------- 获取当前用户信息（无变化） --------------------------
@app.route("/api/v1/user/info", methods=["GET"])
@jwt_required()
def get_user_info():
    current_username = get_jwt_identity()
    return jsonify({
        "code": 200,
        "msg": "获取成功",
        "data": {"username": current_username}
    }), 200


# -------------------------- 启动服务（创建SQLite表） --------------------------
if __name__ == "__main__":
    # 创建SQLite数据库和users表（首次运行自动创建user.db文件）
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

    # 启动Flask服务
    app.run(host="0.0.0.0", port=5000, debug=True)
