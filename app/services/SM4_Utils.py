# app/services/SM4_Utils.py

import os
import base64
import secrets
from gmssl.sm4 import CryptSM4, SM4_ENCRYPT, SM4_DECRYPT


class SM4Service:
    def __init__(self, key_path="app/sm4_key.txt"):
        self.key_path = key_path
        self.key = self._load_or_generate_key()
        self.sm4 = CryptSM4()

    def _load_or_generate_key(self):
        """加载或生成SM4密钥（16字节）"""
        # 确保目录存在
        key_dir = os.path.dirname(self.key_path)
        if key_dir and not os.path.exists(key_dir):
            os.makedirs(key_dir, exist_ok=True)

        # 尝试加载现有密钥
        if os.path.exists(self.key_path):
            try:
                with open(self.key_path, "rb") as f:
                    key = f.read()
                if len(key) == 16:  # SM4密钥必须是16字节
                    print(f"[OK] 已加载现有SM4密钥从: {self.key_path}")
                    return key
            except Exception as e:
                print(f"读取SM4密钥文件出错: {e}")

        # 生成新的SM4密钥
        key = secrets.token_bytes(16)  # 生成16字节随机密钥

        # 保存密钥
        try:
            with open(self.key_path, "wb") as f:
                f.write(key)
            print(f"[OK] 新SM4密钥已生成并保存到: {self.key_path}")
        except Exception as e:
            print(f"保存SM4密钥文件出错: {e}")

        return key

    def encrypt(self, plaintext):
        """SM4加密（ECB模式）"""
        try:
            if isinstance(plaintext, str):
                plaintext = plaintext.encode('utf-8')

            # 设置密钥并加密
            self.sm4.set_key(self.key, SM4_ENCRYPT)
            ciphertext = self.sm4.crypt_ecb(plaintext)

            return base64.b64encode(ciphertext).decode('utf-8')
        except Exception as e:
            print(f"SM4加密错误: {e}")
            # 加密失败时返回base64编码（临时方案）
            if isinstance(plaintext, bytes):
                return base64.b64encode(plaintext).decode('utf-8')
            return base64.b64encode(plaintext.encode('utf-8')).decode('utf-8')

    def decrypt(self, ciphertext_b64):
        """SM4解密（ECB模式）"""
        try:
            ciphertext = base64.b64decode(ciphertext_b64)

            # 设置密钥并解密
            self.sm4.set_key(self.key, SM4_DECRYPT)
            plaintext = self.sm4.crypt_ecb(ciphertext)

            return plaintext.decode('utf-8')
        except Exception as e:
            print(f"SM4解密错误: {e}")
            # 解密失败时尝试base64解码（临时方案）
            try:
                return base64.b64decode(ciphertext_b64).decode('utf-8')
            except:
                return None

    def encrypt_cbc(self, plaintext, iv=None):
        """SM4加密（CBC模式）"""
        try:
            if isinstance(plaintext, str):
                plaintext = plaintext.encode('utf-8')

            # 生成随机IV如果没有提供
            if iv is None:
                iv = secrets.token_bytes(16)
            elif isinstance(iv, str):
                iv = iv.encode('utf-8')

            # 设置密钥并加密
            self.sm4.set_key(self.key, SM4_ENCRYPT)
            ciphertext = self.sm4.crypt_cbc(iv, plaintext)

            # 返回IV+密文的组合
            result = iv + ciphertext
            return base64.b64encode(result).decode('utf-8')
        except Exception as e:
            print(f"SM4 CBC加密错误: {e}")
            return self.encrypt(plaintext)  # 降级到ECB模式

    def decrypt_cbc(self, ciphertext_b64):
        """SM4解密（CBC模式）"""
        try:
            data = base64.b64decode(ciphertext_b64)

            # 提取IV（前16字节）和密文
            iv = data[:16]
            ciphertext = data[16:]

            # 设置密钥并解密
            self.sm4.set_key(self.key, SM4_DECRYPT)
            plaintext = self.sm4.crypt_cbc(iv, ciphertext)

            return plaintext.decode('utf-8')
        except Exception as e:
            print(f"SM4 CBC解密错误: {e}")
            return self.decrypt(ciphertext_b64)  # 降级到ECB模式


# 测试代码
if __name__ == "__main__":
    # 测试SM4服务
    sm4_service = SM4Service("test_sm4_key.txt")

    # 测试ECB模式
    test_str = "Hello, SM4 Encryption!"
    print(f"\n=== 测试SM4 ECB模式 ===")
    print(f"原始数据: {test_str}")

    encrypted = sm4_service.encrypt(test_str)
    print(f"加密结果: {encrypted}")

    decrypted = sm4_service.decrypt(encrypted)
    print(f"解密结果: {decrypted}")

    # 测试CBC模式
    print(f"\n=== 测试SM4 CBC模式 ===")
    encrypted_cbc = sm4_service.encrypt_cbc(test_str)
    print(f"CBC加密结果: {encrypted_cbc}")

    decrypted_cbc = sm4_service.decrypt_cbc(encrypted_cbc)
    print(f"CBC解密结果: {decrypted_cbc}")