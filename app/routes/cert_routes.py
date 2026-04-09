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
    data = request.get_json()
    username = data.get("username", "")
    if not username:
        return jsonify({"code": 400, "msg": "用户名不能为空"}), 400
    try:
        cert = cert_service.issue_user_cert(username)
        return jsonify({
            "code": 200,
            "msg": "证书签发成功",
            "data": cert
        })
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


# 新增：证书登录接口（核心）
@cert_bp.route("/cert-login", methods=["POST"])
def cert_login():
    try:
        client_cert_pem = request.headers.get("X-SSL-CLIENT-CERT")
        if not client_cert_pem:
            return jsonify({"code": 401, "msg": "未检测到客户端证书"}), 401

        client_cert, fingerprint = CertService.verify_client_cert(client_cert_pem, CA_CERT_PATH)

        cert = Certificate.query.filter_by(fingerprint=fingerprint, status=True).first()
        if not cert:
            return jsonify({"code": 401, "msg": "证书未授权或已禁用"}), 401

        if cert.expired_at < datetime.utcnow():
            return jsonify({"code": 401, "msg": "证书已过期"}), 401

        token = generate_token(user_id=cert.user_id)
        return jsonify({
            "code": 200,
            "msg": "证书登录成功",
            "data": {"access_token": token, "expires_in": 7200}
        })
    except Exception as e:
        return jsonify({"code": 401, "msg": f"认证失败：{str(e)}"}), 401