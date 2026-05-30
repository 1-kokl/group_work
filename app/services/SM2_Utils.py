from gmssl.sm2 import CryptSM2, default_ecc_table
import base64
import os
import re
import secrets


def _default_sm2_key_path():
    """与进程工作目录无关，始终指向 app/sm2_key.txt。"""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, "..", "sm2_key.txt"))


def _sig_hex_to_b64url(hex_str):
    """CryptSM2.sign 返回 r||s 十六进制串，编码进 JWT 第三段须可逆解码。"""
    raw = base64.urlsafe_b64encode(hex_str.encode("ascii")).decode("ascii")
    return raw.rstrip("=")


def _sig_b64url_to_hex(segment):
    """JWT 第三段 -> 十六进制签名字符串。"""
    if not segment:
        raise ValueError("empty signature segment")
    pure = re.fullmatch(r"[0-9a-fA-F]{128}", segment)
    if pure:
        return segment.lower()
    s = segment.replace("-", "+").replace("_", "/")
    pad = (4 - len(s) % 4) % 4
    s += "=" * pad
    return base64.b64decode(s).decode("ascii")


def _derive_public_key_from_private(private_key_hex: str) -> str:
    """由私钥 d 计算公钥点 P=d*G（x||y，各 64 位十六进制，无 04 前缀）。"""
    para = len(default_ecc_table["n"])
    placeholder = "0" * (2 * para)
    tmp = CryptSM2(private_key=private_key_hex, public_key=placeholder)
    return tmp._kg(int(private_key_hex, 16), tmp.ecc_table["g"])


class SM2Service:
    def __init__(self, key_path=None):
        self.key_path = key_path or _default_sm2_key_path()
        self.private_key, self.public_key = self._load_or_generate_keys()
        para = len(default_ecc_table["n"])
        pub = (
            self.public_key.lstrip("04")
            if self.public_key.startswith("04")
            else self.public_key
        )
        if len(pub) != 2 * para or not re.fullmatch(r"[0-9a-fA-F]+", pub):
            pub = _derive_public_key_from_private(self.private_key)
            self.public_key = pub
        self.sm2 = CryptSM2(
            private_key=self.private_key,
            public_key=self.public_key,
        )
        self.sm2_c1c3c2 = CryptSM2(
            private_key=self.private_key,
            public_key=self.public_key,
            mode=1,
        )

    def _load_or_generate_keys(self):
        key_dir = os.path.dirname(self.key_path)
        if key_dir and not os.path.exists(key_dir):
            os.makedirs(key_dir, exist_ok=True)
            print(f"[SM2] 创建密钥目录: {key_dir}")

        private_key = None
        stored_public = None

        if os.path.exists(self.key_path):
            try:
                with open(self.key_path, "r", encoding="utf-8") as f:
                    lines = [ln.strip() for ln in f.read().strip().split("\n") if ln.strip()]
                if lines:
                    private_key = lines[0]
                if len(lines) >= 2:
                    cand = lines[1].lstrip("04")
                    if len(cand) == 2 * len(default_ecc_table["n"]) and re.fullmatch(
                        r"[0-9a-fA-F]+", cand
                    ):
                        stored_public = cand
                print(f"[SM2] 已读取私钥: {self.key_path}")
            except Exception as e:
                print(f"[SM2] 读取密钥文件出错: {e}")

        if not private_key:
            print("[SM2] 生成新私钥...")
            private_key = secrets.token_hex(32)

        public_key = _derive_public_key_from_private(private_key)

        if stored_public and stored_public.lower() != public_key.lower():
            print(
                "[SM2] 文件中公钥与私钥不匹配，已按椭圆曲线重新派生公钥并写回（旧 JWT 将失效）"
            )

        try:
            with open(self.key_path, "w", encoding="utf-8") as f:
                f.write(f"{private_key}\n{public_key}\n")
            print(f"[SM2] 密钥对已保存: {self.key_path}")
        except Exception as e:
            print(f"[SM2] 保存密钥文件出错: {e}")

        return private_key, public_key

    def sign(self, data):
        """SM2 签名；返回 Base64URL（内含 hex 的 r||s），与 verify 成对使用。"""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")

            random_hex = secrets.token_hex(32)
            if len(random_hex) < 64:
                random_hex = random_hex.ljust(64, "0")[:64]

            sign = self.sm2.sign(data, random_hex)
            if not sign:
                raise RuntimeError("SM2 sign 返回空")

            if isinstance(sign, bytes):
                sign_hex = sign.hex()
            elif isinstance(sign, str):
                sign_hex = sign
            else:
                sign_hex = str(sign)

            return _sig_hex_to_b64url(sign_hex)
        except Exception as e:
            print(f"签名错误: {e}")
            raise

    def verify(self, data, sign_segment):
        """验证签名：sign_segment 为 JWT 第三段（Base64URL 包裹的 hex，或裸 128 位 hex）。"""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")

            sign_hex = _sig_b64url_to_hex(sign_segment.strip())
            para = len(default_ecc_table["n"])
            if len(sign_hex) != 2 * para or not re.fullmatch(r"[0-9a-fA-F]+", sign_hex):
                return False
            try:
                ok = self.sm2.verify(sign_hex, data)
            except TypeError:
                return False
            return bool(ok)
        except Exception as e:
            print(f"验证签名错误: {e}")
            return False

    def encrypt(self, plaintext):
        """
        SM2 加密。gmssl 的 encrypt 使用随机 k，内部可能得到 None 并触发 len(None)；
        故对 mode=0 / mode=1 交替重试多次。
        """
        if isinstance(plaintext, str):
            data = plaintext.encode("utf-8")
        else:
            data = plaintext

        engines = (self.sm2, self.sm2_c1c3c2)
        last_err = None
        for _ in range(48):
            for eng in engines:
                try:
                    cipher = eng.encrypt(data)
                    if cipher is None:
                        continue
                    if isinstance(cipher, bytes):
                        return base64.b64encode(cipher).decode("utf-8")
                    if isinstance(cipher, str):
                        return base64.b64encode(cipher.encode()).decode("utf-8")
                except (TypeError, AttributeError, ValueError) as e:
                    last_err = e
                    continue
        err_msg = f"SM2 加密失败（已重试）: {last_err}"
        print(f"加密错误: {err_msg}")
        raise RuntimeError(err_msg)

    def decrypt(self, ciphertext_b64):
        """SM2 解密（与 encrypt 使用的 mode=0 / mode=1 对齐）"""
        try:
            cipher = base64.b64decode(ciphertext_b64)
            for eng in (self.sm2, self.sm2_c1c3c2):
                try:
                    plain = eng.decrypt(cipher)
                    if plain is None:
                        continue
                    if isinstance(plain, bytes):
                        return plain.decode("utf-8")
                    return str(plain)
                except Exception:
                    continue
        except Exception as e:
            print(f"解密错误: {e}")
        try:
            return base64.b64decode(ciphertext_b64).decode("utf-8")
        except Exception:
            return None

    def encrypt_json(self, data_dict):
        """加密JSON数据"""
        import json

        try:
            json_str = json.dumps(data_dict, ensure_ascii=False)
            return self.encrypt(json_str)
        except Exception as e:
            print(f"JSON加密错误: {e}")
            return None

    def decrypt_to_json(self, ciphertext_b64):
        """解密JSON数据"""
        import json

        try:
            decrypted_str = self.decrypt(ciphertext_b64)
            if decrypted_str:
                return json.loads(decrypted_str)
            return None
        except Exception as e:
            print(f"JSON解密错误: {e}")
            return None


if __name__ == "__main__":
    sm2_service = SM2Service("sm2_key.txt")
    test_str = "Hello, SM2!"
    encrypted = sm2_service.encrypt(test_str)
    print("decrypt:", sm2_service.decrypt(encrypted))
    sig = sm2_service.sign(test_str.encode("utf-8"))
    print("verify:", sm2_service.verify(test_str.encode("utf-8"), sig))
