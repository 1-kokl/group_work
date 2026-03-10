import gmssl
import base64
import os


class SM4Service:
    def __init__(self, key_path="app/sm4_key.txt"):
        self.key_path = key_path
        self.key = self._load_or_generate_key()
        self.sm4 = gmssl.sm4.SM4()  # 初始化SM4实例

    def _load_or_generate_key(self):
        """加载SM4密钥（16字节），无则生成并保存"""
        try:
            # 读取现有密钥
            with open(self.key_path, "r", encoding="latin-1") as f:
                key = f.read().encode('latin-1')
            if len(key) != 16:
                raise ValueError("SM4密钥必须为16字节")
            return key
        except (FileNotFoundError, ValueError):
            # 生成新密钥（16字节随机数）
            key = os.urandom(16)
            # 保存密钥（latin-1确保字节完整）
            with open(self.key_path, "w", encoding="latin-1") as f:
                f.write(key.decode('latin-1'))
            print(f"✅ 新SM4密钥已生成并保存至 {self.key_path}")
            return key

    def encrypt(self, plaintext):
        """
        SM4-ECB模式加密（适配前端/后端通用）
        :param plaintext: 明文（字符串）
        :return: Base64编码的密文
        """
        if not isinstance(plaintext, str):
            raise TypeError("明文仅支持字符串")

        self.sm4.set_key(self.key, gmssl.sm4.SM4_ENCRYPT)
        # 补位（PKCS7）
        plain_bytes = plaintext.encode('utf-8')
        padding_len = 16 - (len(plain_bytes) % 16)
        plain_bytes += bytes([padding_len] * padding_len)

        cipher_bytes = self.sm4.crypt_ecb(plain_bytes)
        return base64.b64encode(cipher_bytes).decode('utf-8')

    def decrypt(self, ciphertext_b64):
        """
        SM4-ECB模式解密
        :param ciphertext_b64: Base64编码的密文
        :return: 明文（字符串）
        """
        self.sm4.set_key(self.key, gmssl.sm4.SM4_DECRYPT)
        cipher_bytes = base64.b64decode(ciphertext_b64)
        plain_bytes = self.sm4.crypt_ecb(cipher_bytes)
        # 去补位
        padding_len = plain_bytes[-1]
        plain_bytes = plain_bytes[:-padding_len]
        return plain_bytes.decode('utf-8')


# 测试函数（可选）
if __name__ == "__main__":
    sm4 = SM4Service()
    test_phone = "13800000000"
    encrypted = sm4.encrypt(test_phone)
    decrypted = sm4.decrypt(encrypted)
    print(f"原始手机号: {test_phone}")
    print(f"SM4加密后: {encrypted[:30]}...")
    print(f"SM4解密后: {decrypted}")