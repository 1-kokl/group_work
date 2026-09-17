"""第4周应用层安全隧道骨架。

协议：SM4-GCM 加密 JSON Body，SM2 封装一次性会话密钥。
本模块先完成协议字段、密钥生命周期、时间窗和 Nonce 防重放，供 Flask/Axios 接入。
应用层隧道不能替代 HTTPS。
"""
from __future__ import annotations

import base64
import json
import secrets
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from app.services.SM2_Utils import SM2Service


VERSION = "v1"
ALGORITHM = "SM4-GCM+SM2"
KEY_ID = "server-sm2-2026-01"
SESSION_KEY_BYTES = 16
NONCE_BYTES = 12
TAG_BYTES = 16
CLOCK_SKEW_SECONDS = 300
NONCE_TTL_SECONDS = CLOCK_SKEW_SECONDS * 2


class SecureTunnelError(ValueError):
    """信封格式、时间窗、重放或认证标签失败。"""



def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _b64d(value: str) -> bytes:
    try:
        return base64.b64decode(value, validate=True)
    except Exception as exc:
        raise SecureTunnelError("Base64 字段格式错误") from exc


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64urld(value: str) -> bytes:
    try:
        padded = value + "=" * ((4 - len(value) % 4) % 4)
        return base64.urlsafe_b64decode(padded.encode("ascii"))
    except Exception as exc:
        raise SecureTunnelError("Nonce 编码错误") from exc


@dataclass(frozen=True)
class TunnelEnvelope:
    version: str
    key_id: str
    alg: str
    nonce: str
    ts: int
    wrapped_key: str
    ciphertext: str
    tag: str

    @classmethod
    def from_dict(cls, value: Dict[str, Any]) -> "TunnelEnvelope":
        if not isinstance(value, dict):
            raise SecureTunnelError("安全信封必须是 JSON 对象")
        required = {"version", "key_id", "alg", "nonce", "ts", "wrapped_key", "ciphertext", "tag"}
        if set(value) != required:
            raise SecureTunnelError("安全信封字段不完整或包含未知字段")
        try:
            ts = int(value["ts"])
        except (TypeError, ValueError) as exc:
            raise SecureTunnelError("ts 必须是 Unix 秒整数") from exc
        nonce = _b64urld(str(value["nonce"]))
        tag = _b64d(str(value["tag"]))
        if len(nonce) != NONCE_BYTES:
            raise SecureTunnelError("Nonce 必须为 12 字节")
        if len(tag) != TAG_BYTES:
            raise SecureTunnelError("GCM tag 必须为 16 字节")
        for field in ("version", "key_id", "alg", "wrapped_key", "ciphertext"):
            if not isinstance(value[field], str) or not value[field]:
                raise SecureTunnelError(f"{field} 字段不能为空")
        return cls(
            version=value["version"], key_id=value["key_id"], alg=value["alg"],
            nonce=value["nonce"], ts=ts, wrapped_key=value["wrapped_key"],
            ciphertext=value["ciphertext"], tag=value["tag"],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version, "key_id": self.key_id, "alg": self.alg,
            "nonce": self.nonce, "ts": self.ts, "wrapped_key": self.wrapped_key,
            "ciphertext": self.ciphertext, "tag": self.tag,
        }


class NonceStore:
    """演示用线程安全 Nonce 存储；生产环境替换为 Redis/数据库 TTL。"""

    def __init__(self, ttl_seconds: int = NONCE_TTL_SECONDS):
        self.ttl_seconds = ttl_seconds
        self._items: Dict[str, int] = {}
        self._lock = threading.Lock()

    def reserve(self, nonce: str, now: int) -> bool:
        with self._lock:
            self._items = {key: expiry for key, expiry in self._items.items() if expiry > now}
            if nonce in self._items:
                return False
            self._items[nonce] = now + self.ttl_seconds
            return True


class TunnelKeyManager:
    """服务器 SM2 密钥管理入口；会话密钥只在一次请求生命周期内存在。"""

    def __init__(self, key_path: Optional[str] = None, key_id: str = KEY_ID):
        self.key_id = key_id
        self.sm2 = SM2Service(key_path) if key_path else SM2Service()

    @property
    def public_key(self) -> str:
        return self.sm2.public_key

    def wrap_session_key(self, session_key: bytes) -> str:
        if len(session_key) != SESSION_KEY_BYTES:
            raise SecureTunnelError("SM4 会话密钥长度错误")
        # 用 Base64 文本交给 SM2，避免随机二进制直接 UTF-8 解码。
        encoded = base64.b64encode(session_key).decode("ascii")
        return self.sm2.encrypt(encoded)

    def unwrap_session_key(self, wrapped_key: str) -> bytes:
        try:
            key = base64.b64decode(self.sm2.decrypt(wrapped_key), validate=True)
        except Exception as exc:
            raise SecureTunnelError("会话密钥解封失败") from exc
        if len(key) != SESSION_KEY_BYTES:
            raise SecureTunnelError("解封后的会话密钥长度错误")
        return key


class SecureTunnel:
    """纯函数式安全隧道服务，供 Flask 中间件和测试调用。"""

    def __init__(self, key_manager: Optional[TunnelKeyManager] = None,
                 nonce_store: Optional[NonceStore] = None,
                 clock_skew_seconds: int = CLOCK_SKEW_SECONDS):
        self.keys = key_manager or TunnelKeyManager()
        self.nonces = nonce_store or NonceStore()
        self.clock_skew_seconds = clock_skew_seconds

    @staticmethod
    def _aad(version: str, key_id: str, ts: int, nonce: str, method: str, path: str) -> bytes:
        return f"{version}|{key_id}|{ts}|{nonce}|{method.upper()}|{path}".encode("utf-8")

    def seal(self, payload: Dict[str, Any], method: str, path: str,
             now: Optional[int] = None) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            raise SecureTunnelError("payload 必须是 JSON 对象")
        ts = int(time.time() if now is None else now)
        session_key = secrets.token_bytes(SESSION_KEY_BYTES)
        nonce = secrets.token_bytes(NONCE_BYTES)
        nonce_text = _b64url(nonce)
        aad = self._aad(VERSION, self.keys.key_id, ts, nonce_text, method, path)
        plaintext = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
        encryptor = Cipher(algorithms.SM4(session_key), modes.GCM(nonce)).encryptor()
        encryptor.authenticate_additional_data(aad)
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        envelope = TunnelEnvelope(
            version=VERSION, key_id=self.keys.key_id, alg=ALGORITHM,
            nonce=nonce_text, ts=ts, wrapped_key=self.keys.wrap_session_key(session_key),
            ciphertext=_b64(ciphertext), tag=_b64(encryptor.tag),
        )
        return envelope.to_dict()

    def open(self, value: Dict[str, Any], method: str, path: str,
             now: Optional[int] = None) -> Dict[str, Any]:
        envelope = TunnelEnvelope.from_dict(value)
        if envelope.version != VERSION or envelope.alg != ALGORITHM or envelope.key_id != self.keys.key_id:
            raise SecureTunnelError("不支持的安全隧道版本或密钥标识")
        current = int(time.time() if now is None else now)
        if abs(current - envelope.ts) > self.clock_skew_seconds:
            raise SecureTunnelError("请求已超出时间窗")
        if not self.nonces.reserve(envelope.nonce, current):
            raise SecureTunnelError("Nonce 重放")
        nonce = _b64urld(envelope.nonce)
        key = self.keys.unwrap_session_key(envelope.wrapped_key)
        aad = self._aad(envelope.version, envelope.key_id, envelope.ts, envelope.nonce, method, path)
        try:
            decryptor = Cipher(algorithms.SM4(key), modes.GCM(nonce, _b64d(envelope.tag))).decryptor()
            decryptor.authenticate_additional_data(aad)
            plaintext = decryptor.update(_b64d(envelope.ciphertext)) + decryptor.finalize()
            result = json.loads(plaintext.decode("utf-8"))
        except Exception as exc:
            raise SecureTunnelError("密文认证失败") from exc
        if not isinstance(result, dict):
            raise SecureTunnelError("解密结果必须是 JSON 对象")
        return result
