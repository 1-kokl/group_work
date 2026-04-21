from flask import Blueprint, request, jsonify
from app.services.cert_service import CertService
from app.models.ca_models import Certificate
from app import db
from app.utils.jwt_util import generate_token
from datetime import datetime

cert_bp = Blueprint("cert", __name__, url_prefix="/api/cert")
cert_service = CertService()
CA_CERT_PATH = "certs/rootCA.crt"


# 原有：获取根证书
@cert_bp.route("/ca", methods=["GET"])
def get_ca():
    try:
        return jsonify({
            "code": 200,
            "msg": "获取根证书成功",
            "data": cert_service.get_ca_cert()
        })
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


# 原有：签发证书
@cert_bp.route("/issue", methods=["POST"])
def issue_cert():
    from app.services.user_service import user_service
    
    data = request.get_json()
    username = data.get("username", "")
    if not username:
        return jsonify({"code": 400, "msg": "用户名不能为空"}), 400
    try:
        # 检查用户是否存在
        user = user_service.get_user_by_username(username)
        if not user:
            return jsonify({"code": 404, "msg": f"用户 {username} 不存在"}), 404
        
        cert = cert_service.issue_user_cert(username)
        
        # 将证书信息保存到数据库
        import sqlite3
        from cryptography.hazmat.primitives import hashes
        from cryptography import x509 as x509_lib
        from cryptography.hazmat.backends import default_backend
        
        # 计算指纹
        cert_obj = x509_lib.load_pem_x509_certificate(
            cert["certificate"].encode("utf-8"),
            default_backend()
        )
        fingerprint = cert_obj.fingerprint(hashes.SHA256()).hex()
        
        # 获取用户 ID（从 users 表）
        conn = sqlite3.connect('user.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user_row = cursor.fetchone()
        
        if not user_row:
            conn.close()
            return jsonify({"code": 404, "msg": f"用户 {username} 不存在"}), 404
        
        user_id = user_row["id"]
        
        # 检查是否已存在该用户的证书
        cursor.execute("SELECT id FROM certificates WHERE user_id = ?", (user_id,))
        existing_cert = cursor.fetchone()
        
        if existing_cert:
            # 更新现有证书
            cursor.execute(
                """UPDATE certificates 
                   SET fingerprint = ?, serial_number = ?, expired_at = ?, status = 1 
                   WHERE user_id = ?""",
                (fingerprint, str(cert["serial_number"]), cert["not_after"], user_id)
            )
        else:
            # 创建新证书记录
            import uuid
            from datetime import datetime
            cert_id = str(uuid.uuid4())
            cursor.execute(
                """INSERT INTO certificates (id, user_id, fingerprint, serial_number, subject, cert_type, status, issued_at, expired_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    cert_id,
                    user_id,
                    fingerprint,
                    str(cert["serial_number"]),
                    f"CN={username},O=CA-CERT-PLATFORM",
                    "client",
                    1,
                    datetime.utcnow().isoformat(),
                    cert["not_after"]
                )
            )
        
        conn.commit()
        conn.close()
        
        print(f"[DEBUG] 证书已保存到数据库，用户: {username}, 用户ID: {user_id}, 指纹: {fingerprint}")
        
        return jsonify({
            "code": 200,
            "msg": "证书签发成功",
            "data": cert
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"code": 500, "msg": str(e)}), 500


# 新增：证书登录接口（核心）
@cert_bp.route("/cert-login", methods=["POST"])
def cert_login():
    import sqlite3
    
    try:
        print("=" * 50)
        print("[DEBUG] 收到证书登录请求")
        print(f"[DEBUG] Content-Type: {request.content_type}")
        print(f"[DEBUG] 请求头 X-SSL-CLIENT-CERT: {request.headers.get('X-SSL-CLIENT-CERT', 'None')}")
        
        client_cert_pem = None
        
        # 方式1：从请求头获取（适用于 Nginx mTLS 场景）
        client_cert_pem = request.headers.get("X-SSL-CLIENT-CERT")
        
        # 方式2：从请求体获取（适用于前端文件上传场景）
        if not client_cert_pem:
            try:
                data = request.get_json(force=True, silent=True)
                print(f"[DEBUG] 请求体原始数据: {data}")
                if data:
                    client_cert_pem = data.get("cert")
                    print(f"[DEBUG] 从请求体获取的证书长度: {len(client_cert_pem) if client_cert_pem else 0}")
                    print(f"[DEBUG] 证书前100字符: {client_cert_pem[:100] if client_cert_pem else 'None'}")
                else:
                    print("[DEBUG] 请求体为空或无法解析")
            except Exception as e:
                print(f"[DEBUG] 解析请求体失败: {e}")
        
        if not client_cert_pem:
            print("[ERROR] 未检测到客户端证书")
            print("=" * 50)
            return jsonify({"code": 401, "msg": "未检测到客户端证书"}), 401

        print(f"[DEBUG] 开始验证证书，长度: {len(client_cert_pem)}")
        client_cert, fingerprint = CertService.verify_client_cert(client_cert_pem, CA_CERT_PATH)
        print(f"[DEBUG] 证书验证成功，指纹: {fingerprint}")

        # 使用原生 SQLite 查询数据库
        conn = sqlite3.connect('user.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, user_id, fingerprint, serial_number, status, expired_at FROM certificates WHERE fingerprint = ? AND status = 1",
            (fingerprint,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            print(f"[ERROR] 证书未授权，指纹: {fingerprint}")
            print("=" * 50)
            return jsonify({"code": 401, "msg": "证书未授权或已禁用"}), 401

        # 检查证书是否过期
        expired_at_str = row["expired_at"]
        if expired_at_str:
            from datetime import datetime as dt
            expired_at = dt.fromisoformat(expired_at_str) if isinstance(expired_at_str, str) else expired_at
            if expired_at < dt.utcnow():
                print(f"[ERROR] 证书已过期")
                print("=" * 50)
                return jsonify({"code": 401, "msg": "证书已过期"}), 401

        user_id = row["user_id"]
        token = generate_token(user_id=user_id)
        print(f"[SUCCESS] 证书登录成功，用户ID: {user_id}")
        print("=" * 50)
        return jsonify({
            "code": 200,
            "msg": "证书登录成功",
            "data": {"access_token": token, "expires_in": 7200}
        })
    except Exception as e:
        print(f"[ERROR] 认证失败: {str(e)}")
        import traceback
        traceback.print_exc()
        print("=" * 50)
        return jsonify({"code": 401, "msg": f"认证失败：{str(e)}"}), 401


@cert_bp.route("/get", methods=["GET"])
def get_cert():
    """获取用户证书"""
    try:
        cert_pem = cert_service.get_ca_cert()
        return jsonify({
            "code": 200,
            "msg": "获取证书成功",
            "data": {"cert": cert_pem}
        })
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@cert_bp.route("/test", methods=["POST"])
def test_cert():
    """测试证书有效性"""
    data = request.get_json()
    cert_content = data.get("cert", "")
    
    if not cert_content:
        return jsonify({"code": 400, "msg": "证书内容不能为空"}), 400
    
    try:
        is_valid = cert_service.verify_cert_format(cert_content)
        return jsonify({
            "code": 200,
            "msg": "证书测试完成",
            "data": {
                "valid": is_valid,
                "message": "证书格式有效" if is_valid else "证书格式无效"
            }
        })
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@cert_bp.route("/merge", methods=["POST"])
def merge_certs():
    """合并CA证书和用户证书"""
    data = request.get_json()
    ca_cert = data.get("ca_cert", "")
    user_cert = data.get("user_cert", "")
    
    if not ca_cert or not user_cert:
        return jsonify({"code": 400, "msg": "CA证书和用户证书都不能为空"}), 400
    
    try:
        merged_cert = cert_service.merge_certificates(ca_cert, user_cert)
        return jsonify({
            "code": 200,
            "msg": "证书合并成功",
            "data": {
                "merged_cert": merged_cert,
                "length": len(merged_cert)
            }
        })
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500
