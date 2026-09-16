"""
TOTP 软令牌双因素认证服务（RFC 6238）。

设计要点（对应任务书「TOTP 双因素认证」验收）：
- 绑定   ：generate_secret() 生成 Base32 密钥，build_otpauth_uri() 生成扫码串
- 验证   ：verify_totp() 默认在 ±1 个时间步（30s/步）内校验，处理手机时钟轻微偏差（失步处理）
- 防重放 ：verify 返回命中的计数器 counter，由调用方持久化并拒绝「同一窗口重复使用」
- 恢复码 ：generate_recovery_codes() 生成一次性恢复码，hash_recovery_code() 仅存哈希
"""
import base64
import hashlib
import hmac
import secrets
import struct
import time

# 默认参数（与 Google Authenticator / Microsoft Authenticator 兼容）
STEP = 30          # 时间步长（秒）
DIGITS = 6         # 验证码位数
WINDOW = 1         # 容错窗口：±1 步，即最多容忍 60 秒时间偏差
RECOVERY_CODE_COUNT = 10   # 绑定成功后一次性下发的恢复码数量


def _b32_pad(secret: str) -> str:
    """补齐 Base32 长度到 8 的倍数，供解码使用。"""
    secret = (secret or "").upper().rstrip("=")
    return secret + "=" * ((8 - len(secret) % 8) % 8)


def generate_secret(length: int = 20) -> str:
    """生成 Base32 编码的 TOTP 密钥（160 bit 熵，与主流认证器一致）。"""
    return base64.b32encode(secrets.token_bytes(length)).decode("ascii").rstrip("=")


def _hotp(secret: str, counter: int, digits: int = DIGITS) -> str:
    """RFC 4226 HOTP：HMAC-SHA1(key, counter) 动态截断。"""
    key = base64.b32decode(_b32_pad(secret))
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    binary = (
        ((digest[offset] & 0x7F) << 24)
        | (digest[offset + 1] << 16)
        | (digest[offset + 2] << 8)
        | digest[offset + 3]
    )
    return str(binary % (10 ** digits)).zfill(digits)


def totp_at(secret: str, unix_time: int, step: int = STEP, digits: int = DIGITS) -> str:
    """计算某时刻对应的 TOTP 码。"""
    return _hotp(secret, int(unix_time) // step, digits)


def verify_totp(secret: str, code: str, step: int = STEP, window: int = WINDOW, digits: int = DIGITS):
    """
    校验 TOTP 验证码（含时间失步窗口）。

    返回 (ok: bool, counter: int|None)。
    counter 为命中的时间步序号，供上层做「防重放」判断：
    同一 counter 只允许使用一次，可防止同一 30s 窗口内的验证码被重复提交。
    """
    code = (code or "").strip()
    if not code or not secret:
        return False, None
    now = int(time.time())
    for offset in range(-window, window + 1):
        counter = (now // step) + offset
        if hmac.compare_digest(totp_at(secret, now + offset * step, step, digits), code):
            return True, counter
    return False, None


def build_otpauth_uri(username: str, secret: str, issuer: str = "SecureEcommerce") -> str:
    """生成 otpauth:// 协议串，供 Google/Microsoft Authenticator 扫码导入。"""
    label = f"{issuer}:{username}"
    params = f"secret={secret}&issuer={issuer}&algorithm=SHA1&digits={DIGITS}&period={STEP}"
    return f"otpauth://totp/{label}?{params}"


def generate_recovery_codes(count: int = RECOVERY_CODE_COUNT) -> list:
    """生成一次性恢复码（如 AB12-CD34）。仅返回明文，调用方应只保存哈希。"""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # 去除易混淆字符 0/O/1/I
    codes = []
    for _ in range(count):
        raw = "".join(secrets.choice(alphabet) for _ in range(8))
        codes.append(f"{raw[:4]}-{raw[4:]}")
    return codes


def hash_recovery_code(code: str) -> str:
    """恢复码哈希（SHA-256），数据库只存哈希，杜绝明文泄露。"""
    return hashlib.sha256((code or "").strip().upper().encode("utf-8")).hexdigest()


if __name__ == "__main__":
    s = generate_secret()
    print("secret:", s)
    print("uri:", build_otpauth_uri("admin", s))
    now = int(time.time())
    print("code:", totp_at(s, now))
    print("verify:", verify_totp(s, totp_at(s, now)))
    print("recovery:", generate_recovery_codes(3))
