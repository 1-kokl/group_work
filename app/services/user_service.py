
"""用户注册 / 登录 / 查询，与 SQLite user.db 对齐 CLI 注册表结构。"""
import os
import sqlite3
from app.services.SM3_Service import hash_password

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(_ROOT, "user.db")


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def _ensure_table():
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                phone TEXT NOT NULL,
                phone_encrypted TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user'
            )
            """
        )


_ensure_table()


class User:
    __slots__ = ("id", "username", "role", "phone_encrypted")

    def __init__(self, user_id, username, role, phone_encrypted):
        self.id = user_id
        self.username = username
        self.role = role
        self.phone_encrypted = phone_encrypted


class UserService:
    """供 auth_api / user_api 使用；error_msg 为最近一次登录失败原因。"""

    def __init__(self):
        self.error_msg = "用户名或密码错误"

    def register(self, username, password, phone, phone_encrypted):
        pwd_hash = hash_password(password)
        try:
            with _conn() as conn:
                conn.execute(
                    """
                    INSERT INTO users (username, password_hash, phone, phone_encrypted)
                    VALUES (?, ?, ?, ?)
                    """,
                    (username, pwd_hash, phone, phone_encrypted),
                )
            return {"success": True, "msg": ""}
        except sqlite3.IntegrityError:
            return {"success": False, "msg": "用户名已存在"}
        except Exception as e:
            return {"success": False, "msg": str(e)}

    def login(self, username, password):
        self.error_msg = "用户名或密码错误"
        if not username or not password:
            self.error_msg = "用户名和密码不能为空"
            return None
        with _conn() as conn:
            row = conn.execute(
                "SELECT id, username, password_hash, phone_encrypted, role FROM users WHERE username = ?",
                (username,),
            ).fetchone()
        if not row:
            return None
        if row["password_hash"] != hash_password(password):
            return None
        return User(row["id"], row["username"], row["role"] or "user", row["phone_encrypted"])

    def get_user_by_username(self, username):
        with _conn() as conn:
            row = conn.execute(
                "SELECT id, username, phone_encrypted, role FROM users WHERE username = ?",
                (username,),
            ).fetchone()
        if not row:
            return None
        return User(row["id"], row["username"], row["role"] or "user", row["phone_encrypted"])

    def update_user_phone(self, username, encrypted_phone, new_phone_plain):
        try:
            with _conn() as conn:
                cur = conn.execute(
                    """
                    UPDATE users SET phone = ?, phone_encrypted = ?
                    WHERE username = ?
                    """,
                    (new_phone_plain, encrypted_phone, username),
                )
                n = cur.rowcount
            return n > 0
        except Exception:
            return False


user_service = UserService()
