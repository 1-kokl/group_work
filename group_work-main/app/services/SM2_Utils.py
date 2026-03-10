import gmssl
import base64
import os

class SM2Service:
    def __init__(self, key_path="app/sm2_key.txt"):
        self.key_path = key_path
        self.private_key, self.public_key = self._load_or_generate_keys()
        # 初始化SM2实例（C1C2C3格式）
        self.sm2 = gmssl.sm2.CryptSM2(
            private_key=self.private_key,
            public_key=self.public_key,
            mode=gmssl.sm2.C1C2C3
        )

    def _load_or_generate_keys(self):
        """加载SM2密钥对，无则生成并保存"""
        try:
            # 读取现有密钥
            with open(self.key_path, "r", encoding="utf-8") as f:
                keys = f.read().split("\n")
            private_key = keys[0].strip()
            public_key = keys[1].strip()
            if not (private_key and public_key):
                raise ValueError("SM2密钥格式错误")
            return private_key, public_key
        except (FileNotFoundError, ValueError):
            # 生成新密钥对
            private_key = gmssl.sm2.gen_private_key()
            public_key = self.sm2._pk
            # 保存密钥
            with open(self.key_path, "w", encoding="utf-8") as f:
                f.write(f"{private_key}\n{public_key}")
            print(f"✅ 新SM2密钥对已生成并保存至 {self.key_path}")
            return private_key, public_key

    def sign(self, data):
        """
        SM2签名（替代RSA签名，用于JWT）
        :param data: 待签名数据（字符串）
        :return: Base64编码的签名结果
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        # 生成随机数（SM2要求）
        random_hex = gmssl.random_hex(32)
        sign = self.sm2.sign(data, random_hex)
        return base64.b64encode(sign.encode('utf-8')).decode('utf-8')

    def verify(self, data, sign_b64):
        """
        SM2验签
        :param data: 原始数据（字符串）
        :param sign_b64: Base64编码的签名
        :return: 验签结果（bool）
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        sign = base64.b64decode(sign_b64).decode('utf-8')
        return self.sm2.verify(sign, data)

    def encrypt(self, plaintext):
        """SM2加密（可选，用于高敏感数据）"""
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        cipher = self.sm2.encrypt(plaintext)
        return base64.b64encode(cipher).decode('utf-8')

    def decrypt(self, ciphertext_b64):
        """SM2解密（可选）"""
        cipher = base64.b64decode(ciphertext_b64)
        plain = self.sm2.decrypt(cipher)
        return plain.decode('utf-8')

# 测试函数（可选）
if __name__ == "__main__":
    sm2 = SM2Service()
    test_data = "user_login:testuser123"
    sign = sm2.sign(test_data)
    verify_result = sm2.verify(test_data, sign)
    print(f"原始数据: {test_data}")
    print(f"SM2签名: {sign[:30]}...")
    print(f"验签结果: {verify_result}")