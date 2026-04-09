import os
import uuid
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

# 配置路径
CA_KEY_PATH = "certs/rootCA.key"
CA_CERT_PATH = "certs/rootCA.crt"
CERT_VALID_DAYS = 365

class CertService:
    def __init__(self):
        # 初始化时加载CA密钥和证书
        self.ca_key = self._load_ca_key()
        self.ca_cert = self._load_ca_cert()

    def _load_ca_key(self):
        """加载CA私钥"""
        with open(CA_KEY_PATH, "rb") as f:
            return serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )

    def _load_ca_cert(self):
        """加载CA根证书"""
        with open(CA_CERT_PATH, "rb") as f:
            return x509.load_pem_x509_certificate(f.read(), default_backend())

    def get_ca_cert(self):
        """获取根证书PEM内容（你原有接口）"""
        with open(CA_CERT_PATH, "r", encoding="utf-8") as f:
            return f.read()

    def issue_user_cert(self, username: str):
        """签发用户客户端证书（你原有接口）"""
        # 生成用户私钥
        user_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # 证书主题
        subject = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, username),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "CA-CERT-PLATFORM"),
        ])

        # 证书有效期
        now = datetime.utcnow()
        expired_at = now + timedelta(days=CERT_VALID_DAYS)

        # 构建证书
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            self.ca_cert.subject
        ).public_key(
            user_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            now
        ).not_valid_after(
            expired_at
        ).add_extension(
            x509.KeyUsage(digital_signature=True, key_encipherment=True, content_commitment=False,
                          data_encipherment=False, key_agreement=False, key_cert_sign=False, crl_sign=False,
                          encipher_only=False, decipher_only=False),
            critical=True
        ).add_extension(
            x509.ExtendedKeyUsage([x509.ExtendedKeyUsageOID.CLIENT_AUTH]),
            critical=True
        ).sign(
            private_key=self.ca_key,
            algorithm=hashes.SHA256(),
            backend=default_backend()
        )

        # 导出PEM格式
        key_pem = user_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode("utf-8")

        cert_pem = cert.public_bytes(
            encoding=serialization.Encoding.PEM
        ).decode("utf-8")

        # 返回证书信息
        return {
            "username": username,
            "serial_number": cert.serial_number,
            "not_before": now.isoformat(),
            "not_after": expired_at.isoformat(),
            "private_key": key_pem,
            "certificate": cert_pem
        }

    @staticmethod
    def verify_client_cert(client_cert_pem: str, root_ca_path: str):
        """
        验证客户端证书：是否由本CA签发 + 有效期检查
        供登录接口调用
        """
        # 加载根CA证书
        with open(root_ca_path, "rb") as f:
            root_ca = x509.load_pem_x509_certificate(f.read(), default_backend())

        # 清洗证书格式
        clean_cert = client_cert_pem.strip()
        if not clean_cert.startswith("-----BEGIN CERTIFICATE-----"):
            clean_cert = f"-----BEGIN CERTIFICATE-----\n{clean_cert}\n-----END CERTIFICATE-----"

        # 解析客户端证书
        client_cert = x509.load_pem_x509_certificate(
            clean_cert.encode("utf-8"),
            default_backend()
        )

        # 验证证书签名（是否由本CA签发）
        try:
            root_ca.public_key().verify(
                client_cert.signature,
                client_cert.tbs_certificate_bytes,
                hashes.SHA256()
            )
        except Exception:
            raise Exception("证书非法：非本平台CA签发")

        # 验证证书有效期
        now = datetime.utcnow()
        if client_cert.not_valid_after < now or client_cert.not_valid_before > now:
            raise Exception("证书已过期或未生效")

        # 计算证书指纹（用于数据库查询）
        fingerprint = client_cert.fingerprint(hashes.SHA256()).hex()
        return client_cert, fingerprint