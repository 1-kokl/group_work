# app/services/cert.py
from gmssl import sm2, sm3, func
import base64
import os


def generate_sm2_key():
    """
    生成 SM2 密钥对（使用库内部方法）
    """
    # 生成 32 字节私钥（64 个十六进制字符）
    private_key = os.urandom(32).hex()

    # 创建一个临时的 SM2 对象，仅用于计算公钥
    # 注意：有些版本的 CryptSM2 不会自动计算公钥，需要显式调用方法
    tmp = sm2.CryptSM2(private_key=private_key, public_key='')

    # 尝试获取公钥：优先使用内部属性 _public_key，否则尝试其他方式
    if hasattr(tmp, '_public_key'):
        public_key = tmp._public_key
    elif hasattr(tmp, 'public_key'):
        public_key = tmp.public_key
    else:
        # 如果都没有，则手动通过椭圆曲线点乘计算公钥
        # 曲线参数：SM2 的基点 G 坐标（已知），用私钥乘以 G 得到公钥
        # 但这里简单起见，我们使用已知的库函数计算（如果有的话）
        # 如果实在没有，我们可以使用 gmssl.sm2.SM2 的其他构造方式
        raise RuntimeError("无法从私钥自动计算公钥，请检查 gmssl 版本")

    return private_key, public_key


def create_ca_certificate():
    """创建 CA 根证书"""
    ca_pri, ca_pub = generate_sm2_key()

    ca_cert = f"""-----BEGIN SM2 CA CERTIFICATE-----
Issuer: UESTC_CA
Subject: UESTC Root CA
Validity: 2026-03-26 -- 2036-03-26
Public Key: {ca_pub}
Signature Algorithm: SM2withSM3
-----END SM2 CA CERTIFICATE-----"""

    return ca_pri, ca_pub, ca_cert


def issue_user_certificate(ca_pri, ca_pub, user_pub, username="张三"):
    """CA 签发用户证书"""
    # 构造待签名的数据
    data = f"ISSUER=UESTC_CA;SUBJECT={username};PUB={user_pub}".encode()

    # 创建 CA 的 SM2 对象（用于签名）
    ca_sm2 = sm2.CryptSM2(private_key=ca_pri, public_key=ca_pub)

    # 生成签名所需的随机数 K
    # para_len 通常为 32，random_hex(para_len) 返回 64 个十六进制字符
    random_k = func.random_hex(ca_sm2.para_len)

    # 签名：返回结果可能是 bytes 或十六进制字符串
    sig_raw = ca_sm2.sign(data, random_k)

    # 统一转换为 bytes，以便进行 base64 编码
    if isinstance(sig_raw, str):
        # 如果是十六进制字符串，先转为 bytes
        sig = bytes.fromhex(sig_raw)
    else:
        # 如果已经是 bytes，直接使用
        sig = sig_raw

    # 构造用户证书
    user_cert = f"""-----BEGIN SM2 USER CERTIFICATE-----
Version: X509v3
Issuer: UESTC_CA
Subject: {username}
Validity: 2026-03-26 -- 2027-03-26
User Public Key: {user_pub}
CA Signature: {base64.b64encode(sig).decode()}
Signature Algorithm: SM2withSM3
-----END SM2 USER CERTIFICATE-----"""

    return user_cert


# ==================== 测试 ====================
if __name__ == "__main__":
    print("正在生成 CA 根证书...\n")

    # 生成 CA
    ca_pri, ca_pub, ca_crt = create_ca_certificate()
    print("===== CA 根证书 =====")
    print(ca_crt)

    # 生成用户密钥
    user_pri, user_pub = generate_sm2_key()
    print(f"\n用户私钥: {user_pri}")
    print(f"用户公钥: {user_pub}")

    # CA 签发用户证书
    user_crt = issue_user_certificate(ca_pri, ca_pub, user_pub, "张三")
    print("\n===== 用户证书 =====")
    print(user_crt)