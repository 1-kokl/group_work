# app/routes/cert_routes.py
from flask import Blueprint, request, jsonify
from app.services.cert_service import CertService
from datetime import datetime

# 1. 先定义蓝图
cert_bp = Blueprint("cert", __name__, url_prefix="/api/cert")
cert_service = CertService()
CA_CERT_PATH = "certs/rootCA.crt"

# 2. 定义路由

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

@cert_bp.route("/issue", methods=["POST"])
def issue_cert():
    # 【关键修改】在函数内部导入 db，解决循环导入问题
    from app import db 
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
        
        # 将证书信息保存到数据库 (使用原生 SQLite，如你原有代码)
        import sqlite3
        import os
        from cryptography.hazmat.primitives import hashes
        from cryptography import x509 as x509_lib
        from cryptography.hazmat.backends import default_backend
        
        # 计算指纹
        cert_obj = x509_lib.load_pem_x509_certificate(
            cert["certificate"].encode("utf-8"),
            default_backend()
        )
        fingerprint = cert_obj.fingerprint(hashes.SHA256()).hex()
        
        # 获取用户 ID（从 users 表）- 使用绝对路径
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "user.db")
        conn = sqlite3.connect(db_path)
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
        
        # 首先查询证书信息
        cursor.execute(
            "SELECT id, user_id, fingerprint, serial_number, status, expired_at FROM certificates WHERE fingerprint = ? AND status = 1",
            (fingerprint,)
        )
        cert_row = cursor.fetchone()
        
        if not cert_row:
            conn.close()
            print(f"[ERROR] 证书未授权，指纹: {fingerprint}")
            print("=" * 50)
            return jsonify({"code": 401, "msg": "证书未授权或已禁用"}), 401

        # 检查证书是否过期
        expired_at_str = cert_row["expired_at"]
        if expired_at_str:
            from datetime import datetime as dt
            expired_at = dt.fromisoformat(expired_at_str) if isinstance(expired_at_str, str) else expired_at
            if expired_at < dt.utcnow():
                conn.close()
                print(f"[ERROR] 证书已过期")
                print("=" * 50)
                return jsonify({"code": 401, "msg": "证书已过期"}), 401

        # 通过 user_id 获取用户信息
        user_id = cert_row["user_id"]
        cursor.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,))
        user_row = cursor.fetchone()
        conn.close()
        
        if not user_row:
            print(f"[ERROR] 用户不存在，user_id: {user_id}")
            print("=" * 50)
            return jsonify({"code": 404, "msg": "用户不存在"}), 404

        # 生成 JWT Token（使用 SM2 签名）
        from app.services.JWT_SM2_Utils import jwt_service
        tokens = jwt_service.generate_tokens(
            username=user_row["username"],
            role=user_row["role"] or "user",
            user_id=user_row["id"]
        )
        
        print(f"[SUCCESS] 证书登录成功，用户: {user_row['username']}, 用户ID: {user_row['id']}")
        print("=" * 50)
        
        return jsonify({
            "code": 200,
            "msg": "证书登录成功",
            "data": {
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "expires_in": 3600,
                "user": {
                    "username": user_row["username"],
                    "role": user_row["role"] or "user",
                    "auth_method": "certificate"
                }
            }
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
        # 先检查基本格式
        clean_cert = cert_content.strip()
        
        # 检查是否包含 BEGIN/END 标记
        has_begin = "-----BEGIN CERTIFICATE-----" in clean_cert
        has_end = "-----END CERTIFICATE-----" in clean_cert
        
        if not has_begin or not has_end:
            return jsonify({
                "code": 200,
                "msg": "证书测试完成",
                "data": {
                    "valid": False,
                    "message": "证书格式无效：缺少 PEM 标记（-----BEGIN CERTIFICATE----- / -----END CERTIFICATE-----）",
                    "details": {
                        "format": False,
                        "has_begin_marker": has_begin,
                        "has_end_marker": has_end,
                        "content_length": len(clean_cert)
                    }
                }
            })
        
        # 尝试解析证书
        is_valid = cert_service.verify_cert_format(cert_content)
        
        if is_valid:
            return jsonify({
                "code": 200,
                "msg": "证书测试完成",
                "data": {
                    "valid": True,
                    "message": "证书格式有效",
                    "details": {
                        "format": True,
                        "content_length": len(clean_cert)
                    }
                }
            })
        else:
            return jsonify({
                "code": 200,
                "msg": "证书测试完成",
                "data": {
                    "valid": False,
                    "message": "证书格式无效：无法解析为有效的 X.509 证书",
                    "details": {
                        "format": False,
                        "content_length": len(clean_cert)
                    }
                }
            })
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[ERROR] 证书测试失败: {error_detail}")
        return jsonify({
            "code": 500,
            "msg": f"证书测试失败: {str(e)}",
            "data": {
                "valid": False,
                "message": f"服务器内部错误: {str(e)}"
            }
        }), 500

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