"""第4周安全隧道验收：协议、篡改、时间窗、Nonce 重放和 Flask 接入。"""
import copy
import time

import run
from app.services.secure_tunnel import SecureTunnel, SecureTunnelError


METHOD = "POST"
PATH = "/api/v1/tunnel/echo"


def expect_reject(tunnel, envelope, reason, now=None):
    try:
        tunnel.open(envelope, METHOD, PATH, now=now)
    except SecureTunnelError as exc:
        print(f"[PASS] {reason}: {exc}")
        return
    raise AssertionError(f"{reason}: 请求未被拒绝")


def main():
    tunnel = SecureTunnel()
    now = int(time.time())
    payload = {"order_id": "W4-DEMO-001", "amount": 99.5, "receiver": "脱敏演示"}

    # 1. 正常封装/解封
    envelope = tunnel.seal(payload, METHOD, PATH, now=now)
    assert set(envelope) == {"version", "key_id", "alg", "nonce", "ts", "wrapped_key", "ciphertext", "tag"}
    assert "W4-DEMO-001" not in envelope["ciphertext"]
    assert tunnel.open(envelope, METHOD, PATH, now=now) == payload
    print("[PASS] 正常 SM4-GCM 加密、SM2 封装和解封")

    # 2. 同一 Nonce 重放
    expect_reject(tunnel, envelope, "Nonce 重放", now=now)

    # 3. 修改密文，GCM tag 必须失败
    tampered = tunnel.seal(payload, METHOD, PATH, now=now)
    tampered["ciphertext"] = ("A" if tampered["ciphertext"][0] != "A" else "B") + tampered["ciphertext"][1:]
    expect_reject(tunnel, tampered, "密文篡改", now=now)

    # 4. 修改 tag
    tag_tampered = tunnel.seal(payload, METHOD, PATH, now=now)
    tag_tampered["tag"] = ("A" if tag_tampered["tag"][0] != "A" else "B") + tag_tampered["tag"][1:]
    expect_reject(tunnel, tag_tampered, "认证标签篡改", now=now)

    # 5. 时间窗过期
    expired = tunnel.seal(payload, METHOD, PATH, now=now - 601)
    expect_reject(tunnel, expired, "时间窗过期", now=now)

    # 6. 方法/路径绑定
    wrong_path = tunnel.seal(payload, METHOD, PATH, now=now)
    try:
        tunnel.open(wrong_path, METHOD, "/api/v1/tunnel/other", now=now)
    except SecureTunnelError as exc:
        print(f"[PASS] AAD 方法/路径绑定: {exc}")
    else:
        raise AssertionError("AAD 方法/路径绑定未生效")

    # 7. Flask 演示接口：成功返回新的加密信封
    client = run.app.test_client()
    request_env = tunnel.seal(payload, METHOD, PATH)
    response = client.post(PATH, json=request_env)
    assert response.status_code == 200, response.get_json()
    body = response.get_json()
    assert body["data"]["alg"] == "SM4-GCM+SM2"
    response_payload = tunnel.open(body["data"], METHOD, PATH)
    assert response_payload["echo"] == payload
    print("[PASS] Flask /api/v1/tunnel/echo 端到端封装响应")

    # 8. Flask 拒绝重放
    replay = client.post(PATH, json=request_env)
    assert replay.status_code == 400, replay.get_json()
    print("[PASS] Flask 接口拒绝重复 Nonce")

    print("第4周安全隧道验收：全部通过")


if __name__ == "__main__":
    main()
