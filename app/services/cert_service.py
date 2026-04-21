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
CERT_VALID_DAYS = 1095

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
        from cryptography.hazmat.primitives.asymmetric import padding
        
        with open(root_ca_path, "rb") as f:
            root_ca = x509.load_pem_x509_certificate(f.read(), default_backend())

        clean_cert = client_cert_pem.strip()
        if not clean_cert.startswith("-----BEGIN CERTIFICATE-----"):
            clean_cert = f"-----BEGIN CERTIFICATE-----\n{clean_cert}\n-----END CERTIFICATE-----"

        client_cert = x509.load_pem_x509_certificate(
            clean_cert.encode("utf-8"),
            default_backend()
        )

        try:
            root_ca.public_key().verify(
                client_cert.signature,
                client_cert.tbs_certificate_bytes,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
        except Exception as e:
            print(f"[DEBUG] 证书验证失败原因: {str(e)}")
            raise Exception("证书非法：非本平台CA签发")

        now = datetime.utcnow()
        if client_cert.not_valid_after < now or client_cert.not_valid_before > now:
            raise Exception("证书已过期或未生效")

        fingerprint = client_cert.fingerprint(hashes.SHA256()).hex()
        return client_cert, fingerprint

    @staticmethod
    def verify_cert_format(cert_content: str) -> bool:
        """
        验证证书格式是否有效
        :param cert_content: PEM格式的证书内容
        :return: True 如果格式有效，False 否则
        """
        try:
            if not cert_content or not isinstance(cert_content, str):
                return False
            
            clean_cert = cert_content.strip()
            
            if not clean_cert.startswith("-----BEGIN CERTIFICATE-----"):
                clean_cert = f"-----BEGIN CERTIFICATE-----\n{clean_cert}\n-----END CERTIFICATE-----"
            
            x509.load_pem_x509_certificate(
                clean_cert.encode("utf-8"),
                default_backend()
            )
            return True
        except Exception:
            return False

    @staticmethod
    def merge_certificates(ca_cert_pem: str, user_cert_pem: str) -> str:
        """
        合并CA证书和用户证书为完整的证书链
        :param ca_cert_pem: CA根证书PEM内容
        :param user_cert_pem: 用户证书PEM内容
        :return: 合并后的证书链PEM内容
        """
        try:
            ca_cert = ca_cert_pem.strip()
            user_cert = user_cert_pem.strip()
            
            if not ca_cert or not user_cert:
                raise ValueError("证书内容不能为空")
            
            merged = f"{user_cert}\n{ca_cert}"
            return merged
        except Exception as e:
            raise Exception(f"证书合并失败: {str(e)}")
