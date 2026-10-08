from functools import wraps

from flask import request

from app.services.audit_service import write_log
from app.utils.response import api_response
from app.services.secure_tunnel import SecureTunnelError


# 只对明确加入白名单的路由启用该装饰器；普通接口保持原有 JSON 行为。
def secure_tunnel_required(tunnel):
    """解密应用层安全信封并把明文放到 request.decrypted_json。"""
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            envelope = request.get_json(silent=True)
            try:
                if request.query_string or (request.content_length or 0) > 65536:
                    raise SecureTunnelError("Unsupported query or oversized body")
                plaintext, session_key = tunnel.open_request(
                    envelope,
                    request.method,
                    request.path,
                )
            except SecureTunnelError as exc:
                write_log(
                    action="SECURE_TUNNEL_REJECT",
                    resource=request.path,
                    result="denied",
                    ip=request.remote_addr,
                    detail=str(exc),
                )
                return api_response(400, "安全隧道请求校验失败")

            request.decrypted_json = plaintext
            request.tunnel_session_key = session_key
            request.tunnel_envelope = envelope
            write_log(
                action="SECURE_TUNNEL_ACCEPT",
                resource=request.path,
                result="success",
                ip=request.remote_addr,
                detail=f"alg={tunnel.keys.key_id}",
            )
            try:
                return view(*args, **kwargs)
            finally:
                del request.tunnel_session_key

        return wrapped
    return decorator
