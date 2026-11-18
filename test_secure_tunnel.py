"""Week 4 acceptance: protocol, tamper, expiry, replay and real Flask response."""
import copy, time
import run
from app.services.secure_tunnel import SecureTunnel, SecureTunnelError, VERSION, ALGORITHM
METHOD, PATH = "POST", "/api/v1/tunnel/echo"

def reject(fn, reason):
    try: fn()
    except SecureTunnelError as exc: print(f"[PASS] {reason}: {exc}"); return
    raise AssertionError(reason + ": request was accepted")

def main():
    tunnel = SecureTunnel(nonce_store=__import__('app.services.secure_tunnel', fromlist=['NonceStore']).NonceStore())
    now = int(time.time()); payload = {"order_id":"W4-DEMO-001", "amount":99.5, "receiver":"脱敏演示"}
    env, key = tunnel.seal_request(payload, METHOD, PATH, now)
    assert set(env) == {"version","key_id","alg","nonce","ts","wrapped_key","ciphertext","tag"}
    assert tunnel.open(env, METHOD, PATH, now) == payload
    print("[PASS] 正常 SM4-GCM 加密、SM2 封装和解封")
    reject(lambda: tunnel.open(env, METHOD, PATH, now), "Nonce 重放")
    tampered, _ = tunnel.seal_request(payload, METHOD, PATH, now); tampered['ciphertext'] = ('A' if tampered['ciphertext'][0]!='A' else 'B')+tampered['ciphertext'][1:]
    reject(lambda: tunnel.open(tampered, METHOD, PATH, now), "密文篡改")
    tagged, _ = tunnel.seal_request(payload, METHOD, PATH, now); tagged['tag'] = ('A' if tagged['tag'][0]!='A' else 'B')+tagged['tag'][1:]
    reject(lambda: tunnel.open(tagged, METHOD, PATH, now), "认证标签篡改")
    expired, _ = tunnel.seal_request(payload, METHOD, PATH, now-601)
    reject(lambda: tunnel.open(expired, METHOD, PATH, now), "时间窗过期")
    wrong, _ = tunnel.seal_request(payload, METHOD, PATH, now)
    reject(lambda: tunnel.open(wrong, METHOD, '/api/v1/tunnel/other', now), "AAD 方法/路径绑定")
    client = run.app.test_client(); request_env, request_key = tunnel.seal_request(payload, METHOD, PATH)
    response = client.post(PATH, json=request_env); assert response.status_code == 200, response.get_json()
    body = response.get_json(); assert body['data']['version'] == VERSION and body['data']['alg'] == ALGORITHM
    response_payload = tunnel.open_response(body['data'], request_env, request_key, METHOD, PATH)
    assert response_payload['echo'] == payload
    print('[PASS] Flask /api/v1/tunnel/echo 端到端封装响应')
    replay = client.post(PATH, json=request_env); assert replay.status_code == 400
    print('[PASS] Flask 接口拒绝重复 Nonce')
    print('第4周安全隧道验收：全部通过')
if __name__ == '__main__': main()
