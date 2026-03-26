from app.services.cert import create_ca_certificate, issue_user_certificate, generate_sm2_key
import os

# 证书存储目录
CERT_DIR = "certs"
CA_PRIVATE_PATH = os.path.join(CERT_DIR, "ca_private.key")
CA_CERT_PATH = os.path.join(CERT_DIR, "ca_cert.pem")

os.makedirs(CERT_DIR, exist_ok=True)

class CertService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.init_ca()
        return cls._instance

    def init_ca(self):
        # 加载已存在的 CA，不存在就创建
        if os.path.exists(CA_PRIVATE_PATH) and os.path.exists(CA_CERT_PATH):
            with open(CA_PRIVATE_PATH, "r", encoding="utf-8") as f:
                self.ca_pri = f.read().strip()
            with open(CA_CERT_PATH, "r", encoding="utf-8") as f:
                self.ca_cert = f.read().strip()

            # 从证书提取公钥
            for line in self.ca_cert.split("\n"):
                if line.startswith("Public Key:"):
                    self.ca_pub = line.replace("Public Key:", "").strip()
                    break
        else:
            self.ca_pri, self.ca_pub, self.ca_cert = create_ca_certificate()
            with open(CA_PRIVATE_PATH, "w", encoding="utf-8") as f:
                f.write(self.ca_pri)
            with open(CA_CERT_PATH, "w", encoding="utf-8") as f:
                f.write(self.ca_cert)

    def get_ca_cert(self):
        return self.ca_cert

    def issue_user_cert(self, username):
        user_pri, user_pub = generate_sm2_key()
        user_cert = issue_user_certificate(
            self.ca_pri,
            self.ca_pub,
            user_pub,
            username
        )
        return {
            "username": username,
            "user_private_key": user_pri,
            "user_public_key": user_pub,
            "user_certificate": user_cert,
            "ca_certificate": self.ca_cert
        }