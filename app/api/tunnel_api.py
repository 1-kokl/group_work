from flask import Blueprint, request

from app.middleware.secure_tunnel import secure_tunnel_required
from app.services.secure_tunnel import SecureTunnel, VERSION, ALGORITHM
from app.utils.response import api_response


tunnel_bp = Blueprint("secure_tunnel", __name__, url_prefix="/api/v1/tunnel")
tunnel = SecureTunnel()


@tunnel_bp.get("/config")
def tunnel_config():
    """返回前端封装信封所需的公开参数；绝不返回服务端私钥。"""
    return api_response(200, "安全隧道配置", {
        "version": VERSION,
        "alg": ALGORITHM,
        "key_id": tunnel.keys.key_id,
        "sm2_public_key": tunnel.keys.public_key,
        "clock_skew_seconds": tunnel.clock_skew_seconds,
    })


@tunnel_bp.post("/echo")
@secure_tunnel_required(tunnel)
def tunnel_echo():
    """第4周演示接口：解密请求后返回同样通过隧道保护的响应。"""
    payload = getattr(request, "decrypted_json", None)
    response_payload = {"echo": payload, "transport": "secure-tunnel", "key_id": tunnel.keys.key_id}
    envelope = tunnel.seal_response(response_payload, request.tunnel_envelope,
                                    request.tunnel_session_key, "POST", request.path)
    return api_response(200, "安全隧道处理成功", envelope)
