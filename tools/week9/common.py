"""Shared paths and isolation for local acceptance tooling."""
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / ".local" / "week9"
TOOL_PACKAGES = ROOT / ".local" / "tools" / "python"


def configure(directory, source=ROOT):
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(TOOL_PACKAGES))
    sys.path.insert(0, str(source))
    os.environ.update({
        "APP_USER_DB_PATH": str(directory / "app.sqlite3"),
        "APP_ECOMMERCE_DB_PATH": str(directory / "app.sqlite3"),
        "APP_AUDIT_DB_PATH": str(directory / "audit.sqlite3"),
        "APP_SM2_KEY_PATH": str(directory / "keys" / "sm2.txt"),
        "APP_SM4_KEY_PATH": str(directory / "keys" / "sm4.bin"),
        "APP_TUNNEL_DIR": str(directory / "tunnel"),
        "APP_CA_KEY_PATH": str(directory / "keys" / "ca.key"),
        "APP_CA_CERT_PATH": str(directory / "keys" / "ca.crt"),
        "PYTHONDONTWRITEBYTECODE": "1",
    })
    (directory / "keys").mkdir(exist_ok=True)
    if not (directory / "keys" / "ca.key").exists():
        from datetime import datetime, timedelta, timezone
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Local acceptance CA")])
        now = datetime.now(timezone.utc)
        cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
                .public_key(key.public_key()).serial_number(x509.random_serial_number())
                .not_valid_before(now - timedelta(days=1)).not_valid_after(now + timedelta(days=30))
                .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
                .sign(key, hashes.SHA256()))
        (directory / "keys" / "ca.key").write_bytes(key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        (directory / "keys" / "ca.crt").write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    return directory
