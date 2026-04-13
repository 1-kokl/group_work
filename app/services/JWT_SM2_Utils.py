import time
import json
import base64
from .SM2_Utils import SM2Service  # 这里你已经加了点 ✔️ 正确

class JWTSM2Service:
    def __init__(self):
        self.sm2_service = SM2Service()
        self._token_blacklist = set()
        # JWT头部（自定义，标识SM2算法）
        self.header = {
            "alg": "SM2",
            "typ": "JWT"
        }

    def _base64_encode(self, data):
        """JWT标准Base64编码（无填充）"""
        if isinstance(data, dict):
            data = json.dumps(data, separators=(',', ':')).encode('utf-8')
        b64 = base64.b64encode(data).decode('utf-8')
        return b64.replace('+', '-').replace('/', '_').rstrip('=')

    def _base64_decode(self, b64_str):
        """JWT标准Base64解码"""
        b64_str = b64_str.replace('-', '+').replace('_', '/')
        padding = 4 - (len(b64_str) % 4)
        b64_str += '=' * padding
        return base64.b64decode(b64_str)

    def generate_token(self, payload, expires_in=3600):
        """
        生成SM2签名的JWT令牌
        :param payload: JWT载荷（字典）
        :param expires_in: 过期时间（秒）
        :return: JWT令牌字符串
        """
        payload = dict(payload)
        # 添加过期时间
        payload["exp"] = int(time.time()) + expires_in
        # 编码头部和载荷
        header_b64 = self._base64_encode(self.header)
        payload_b64 = self._base64_encode(payload)
        # 拼接待签名数据
        sign_data = f"{header_b64}.{payload_b64}".encode('utf-8')
        # SM2签名
        sign_b64 = self.sm2_service.sign(sign_data)
        # 拼接最终JWT
        return f"{header_b64}.{payload_b64}.{sign_b64}"

    def verify_token(self, token):
        """
        验证SM2签名的JWT令牌
        :param token: JWT令牌字符串
        :return: 验证通过返回载荷，失败抛出异常
        """
        try:
            if token in self._token_blacklist:
                raise RuntimeError("Token已注销")
            # 拆分JWT
            header_b64, payload_b64, sign_b64 = token.split('.')
            # 验证签名
            sign_data = f"{header_b64}.{payload_b64}".encode('utf-8')
            if not self.sm2_service.verify(sign_data, sign_b64):
                raise RuntimeError("SM2验签失败")
            # 解码载荷并检查过期时间
            payload = json.loads(self._base64_decode(payload_b64))
            if payload.get("exp", 0) < int(time.time()):
                raise RuntimeError("Token已过期")
            return payload
        except Exception as e:
            raise RuntimeError(f"Token验证失败: {str(e)}")

    def generate_tokens(self, username, role="user"):
        access_token = self.generate_token(
            {"username": username, "role": role}, expires_in=3600
        )
        refresh_token = self.generate_token(
            {"username": username, "role": role, "typ": "refresh"},
            expires_in=604800,
        )
        return {"access_token": access_token, "refresh_token": refresh_token}

    def refresh_access_token(self, refresh_token):
        try:
            payload = self.verify_token(refresh_token)
            if payload.get("typ") != "refresh":
                return None
            username = payload.get("username")
            role = payload.get("role", "user")
            return self.generate_token(
                {"username": username, "role": role}, expires_in=3600
            )
        except Exception:
            return None

    def add_to_blacklist(self, token):
        self._token_blacklist.add(token)

# ====================== ✅【唯一修改：在这里添加这一行】======================
# 作用：创建一个可以被外部导入的 jwt_service 实例
jwt_service = JWTSM2Service()
# ====================== ✅ 修改结束 ======================

# 测试函数（可选）
if __name__ == "__main__":
    jwt_sm2 = JWTSM2Service()
    payload = {"username": "testuser123", "role": "user"}
    token = jwt_sm2.generate_token(payload)
    print(f"SM2-JWT令牌: {token[:50]}...")
    try:
        payload = jwt_sm2.verify_token(token)
        print(f"Token验证通过，载荷: {payload}")
    except Exception as e:
        print(f"Token验证失败: {e}")