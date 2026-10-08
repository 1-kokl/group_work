"""Week 4 v2: SM4-GCM + strict SM2 C1C3C2; HTTPS remains required."""
from __future__ import annotations
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import threading
import time
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from gmssl.sm2 import CryptSM2, default_ecc_table
from gmssl import sm3

VERSION = "v2"
ALGORITHM = "SM4-GCM+SM2"
CLOCK_SKEW_SECONDS = 300
NONCE_TTL_SECONDS = 601
LOCAL_DIR = Path(__file__).resolve().parents[2] / ".local" / "week4"
REQUEST_FIELDS = {"version", "key_id", "alg", "nonce", "ts", "wrapped_key", "ciphertext", "tag"}
RESPONSE_FIELDS = (REQUEST_FIELDS - {"wrapped_key"}) | {"request_nonce"}

class SecureTunnelError(ValueError):
    pass

def _b64(value):
    return base64.b64encode(value).decode("ascii")

def _b64d(value):
    try:
        if not isinstance(value, str):
            raise ValueError()
        raw = base64.b64decode(value, validate=True)
        if _b64(raw) != value:
            raise ValueError()
        return raw
    except Exception as exc:
        raise SecureTunnelError("Invalid canonical Base64") from exc

def _nonce(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{16}", value):
        raise SecureTunnelError("Nonce must be 12 bytes, unpadded Base64URL")
    return base64.urlsafe_b64decode(value)

def new_nonce():
    return base64.urlsafe_b64encode(secrets.token_bytes(12)).decode("ascii")

def response_key(key, request_nonce):
    return HKDF(algorithm=hashes.SHA256(), length=16, salt=_nonce(request_nonce),
                info=b"week4-v2-response").derive(key)

def aad(env, method, path, direction="request", status=200):
    if "?" in path or "|" in path:
        raise SecureTunnelError("Query strings and separator paths are not supported")
    parts = [VERSION, ALGORITHM, env["key_id"], str(env["ts"]), env["nonce"],
             method.upper(), path, direction]
    if direction == "response":
        parts += [env["request_nonce"], str(status)]
    return "|".join(parts).encode("utf-8")

def _encrypt(payload, key, env, method, path, direction="request", status=200):
    if not isinstance(payload, dict):
        raise SecureTunnelError("Body must be a JSON object")
    plaintext = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    enc = Cipher(algorithms.SM4(key), modes.GCM(_nonce(env["nonce"]))).encryptor()
    enc.authenticate_additional_data(aad(env, method, path, direction, status))
    env["ciphertext"] = _b64(enc.update(plaintext) + enc.finalize())
    env["tag"] = _b64(enc.tag)
    return env

def _validate(env, key_id, now, direction="request"):
    fields = REQUEST_FIELDS if direction == "request" else RESPONSE_FIELDS
    if not isinstance(env, dict) or set(env) != fields:
        raise SecureTunnelError("Missing or unknown envelope fields")
    if env["version"] != VERSION or env["alg"] != ALGORITHM or env["key_id"] != key_id:
        raise SecureTunnelError("Unsupported version, algorithm or key ID")
    if type(env["ts"]) is not int or abs(now - env["ts"]) > CLOCK_SKEW_SECONDS:
        raise SecureTunnelError("Invalid timestamp or outside time window")
    _nonce(env["nonce"])
    if len(_b64d(env["tag"])) != 16 or not _b64d(env["ciphertext"]):
        raise SecureTunnelError("Invalid ciphertext or GCM tag length")

def _decrypt(env, key, method, path, direction="request", status=200):
    try:
        dec = Cipher(algorithms.SM4(key), modes.GCM(_nonce(env["nonce"]), _b64d(env["tag"]))).decryptor()
        dec.authenticate_additional_data(aad(env, method, path, direction, status))
        value = json.loads((dec.update(_b64d(env["ciphertext"])) + dec.finalize()).decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError()
        return value
    except Exception as exc:
        raise SecureTunnelError("Ciphertext authentication failed") from exc

class NonceStore:
    """Isolated in-memory store for tests."""
    def __init__(self):
        self._items = {}
        self._lock = threading.Lock()
    def reserve(self, nonce, now):
        with self._lock:
            self._items = {k: v for k, v in self._items.items() if v > now}
            if nonce in self._items:
                return False
            self._items[nonce] = now + NONCE_TTL_SECONDS
            return True

class SQLiteNonceStore:
    """Atomic replay checks shared by local workers and preserved over restarts."""
    def __init__(self, path=None):
        self.path = Path(path or LOCAL_DIR / "replay.sqlite3")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS nonces (nonce TEXT PRIMARY KEY, expires INTEGER NOT NULL)")
    def reserve(self, nonce, now):
        with sqlite3.connect(self.path, timeout=10) as db:
            db.execute("DELETE FROM nonces WHERE expires <= ?", (now,))
            result = db.execute("INSERT OR IGNORE INTO nonces VALUES (?, ?)", (nonce, now + NONCE_TTL_SECONDS))
            return result.rowcount == 1

class TunnelKeyManager:
    """Dedicated ignored local key; do not reuse the published repository demo key."""
    def __init__(self, key_path=None):
        path = Path(key_path or os.environ.get("WEEK4_SM2_KEY_FILE", LOCAL_DIR / "sm2.json"))
        path.parent.mkdir(parents=True, exist_ok=True)
        n = int(default_ecc_table["n"], 16)
        try:
            with path.open("x", encoding="utf-8") as f:
                json.dump({"private_key": f"{secrets.randbelow(n - 1) + 1:064x}"}, f)
        except FileExistsError:
            pass
        private = json.loads(path.read_text(encoding="utf-8"))["private_key"]
        if not re.fullmatch(r"[0-9a-f]{64}", private) or not 0 < int(private, 16) < n:
            raise RuntimeError("Invalid tunnel private key file")
        self._engine = CryptSM2(private_key=private, public_key="", mode=1)
        self.public_key = self._engine._kg(int(private, 16), default_ecc_table["g"])
        self._engine.public_key = self.public_key
        self.key_id = "sm2-" + hashlib.sha256(bytes.fromhex(self.public_key)).hexdigest()[:16]
    def wrap_session_key(self, key):
        if len(key) != 16:
            raise SecureTunnelError("Session key must be 16 bytes")
        return _b64(self._engine.encrypt(key))
    def unwrap_session_key(self, wrapped):
        # gmssl.decrypt does not verify C3; authenticate C3 explicitly.
        try:
            raw = _b64d(wrapped)
            if len(raw) != 112:
                raise ValueError()
            c1, c3 = raw[:64], raw[64:96]
            x, y = int.from_bytes(c1[:32], "big"), int.from_bytes(c1[32:], "big")
            p, a, b = (int(default_ecc_table[k], 16) for k in ("p", "a", "b"))
            if x >= p or y >= p or (y*y - x*x*x - a*x - b) % p:
                raise ValueError()
            key = self._engine.decrypt(raw)
            point = bytes.fromhex(self._engine._kg(int(self._engine.private_key, 16), c1.hex()))
            expected = bytes.fromhex(sm3.sm3_hash(list(point[:32] + key + point[32:])))
            if len(key) != 16 or not hmac.compare_digest(c3, expected):
                raise ValueError()
            return key
        except Exception as exc:
            raise SecureTunnelError("SM2 key wrap authentication failed") from exc

class SecureTunnel:
    def __init__(self, key_manager=None, nonce_store=None):
        self.keys = key_manager or TunnelKeyManager()
        self.nonces = nonce_store if nonce_store is not None else SQLiteNonceStore()
        self.clock_skew_seconds = CLOCK_SKEW_SECONDS
    def seal_request(self, payload, method, path, now=None):
        key = secrets.token_bytes(16)
        env = dict(version=VERSION, alg=ALGORITHM, key_id=self.keys.key_id,
                   nonce=new_nonce(), ts=int(time.time() if now is None else now),
                   wrapped_key=self.keys.wrap_session_key(key))
        return _encrypt(payload, key, env, method, path), key
    def seal(self, payload, method, path, now=None):
        return self.seal_request(payload, method, path, now)[0]
    def open_request(self, env, method, path, now=None):
        now = int(time.time() if now is None else now)
        _validate(env, self.keys.key_id, now)
        key = self.keys.unwrap_session_key(env["wrapped_key"])
        payload = _decrypt(env, key, method, path)
        if not self.nonces.reserve(self.keys.key_id + ":" + env["nonce"], now):
            raise SecureTunnelError("Nonce replay")
        return payload, key
    def open(self, env, method, path, now=None):
        return self.open_request(env, method, path, now)[0]
    def seal_response(self, payload, request_env, key, method, path, status=200):
        env = dict(version=VERSION, alg=ALGORITHM, key_id=self.keys.key_id,
                   nonce=new_nonce(), ts=int(time.time()), request_nonce=request_env["nonce"])
        return _encrypt(payload, response_key(key, env["request_nonce"]), env, method, path, "response", status)
    @staticmethod
    def open_response(env, request_env, key, method, path, status=200):
        _validate(env, request_env["key_id"], int(time.time()), "response")
        if env["request_nonce"] != request_env["nonce"]:
            raise SecureTunnelError("Response does not match request")
        return _decrypt(env, response_key(key, env["request_nonce"]), method, path, "response", status)
