from flask import Blueprint, request, jsonify
from app.services.cert_service import CertService

cert_bp = Blueprint("cert", __name__, url_prefix="/api/cert")
cert_service = CertService()

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