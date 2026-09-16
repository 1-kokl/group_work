"""用户注册 / 登录 / 查询，与 SQLite user.db 对齐 CLI 注册表结构。

本阶段新增（RBAC + MFA）：
- 列迁移：totp_secret / totp_enabled / totp_bound_at / recovery_codes / last_totp_counter / status
- 角色管理：list_users / change_role / set_user_status / reset_password
- TOTP 状态：save_totp_secret / enable_totp / disable_totp / reset_totp
- 恢复码：consume_recovery_code（一次性）
- 防重放：get_last_totp_counter / set_last_totp_counter
"""
import json
import os
import sqlite3

from app.services.SM3_Service import hash_password

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(_ROOT, "user.db")

VALID_ROLES = ("user", "merchant", "admin", "auditor")


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def _ensure_table():
    """确保表结构存在，如果不存在则创建"""
    try:
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
            conn.commit()
    except Exception as e:
        print(f"⚠️ 确保表结构时出错: {e}")


def _migrate():
    """增量迁移：为 users 表补齐 RBAC/MFA 所需列（幂等）。"""
    new_columns = {
        "totp_secret": "TEXT",
        "totp_enabled": "INTEGER NOT NULL DEFAULT 0",
        "totp_bound_at": "TEXT",
        "recovery_codes": "TEXT",           # JSON 数组，仅存恢复码哈希
        "last_totp_counter": "INTEGER NOT NULL DEFAULT 0",
        "status": "INTEGER NOT NULL DEFAULT 1",  # 1=启用 0=禁用
    }
    try:
        with _conn() as conn:
            existing = {r["name"] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
            for col, ddl in new_columns.items():
                if col not in existing:
                    conn.execute(f"ALTER TABLE users ADD COLUMN {col} {ddl}")
            conn.commit()
    except Exception as e:
        print(f"⚠️ users 表迁移出错: {e}")


# 模块加载时确保表存在并完成迁移
_ensure_table()
_migrate()


class User:
    __slots__ = ("id", "username", "role", "phone_encrypted")

    def __init__(self, user_id, username, role, phone_encrypted):
        self.id = user_id
        self.username = username
        self.role = role
        self.phone_encrypted = phone_encrypted


class UserService:
    """供 auth_api / user_api / admin_api 使用；error_msg 为最近一次登录失败原因。"""

    def __init__(self):
        self.error_msg = "用户名或密码错误"

    # ---------- 注册 / 登录 ----------

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
                "SELECT id, username, password_hash, phone_encrypted, role, status FROM users WHERE username = ?",
                (username,),
            ).fetchone()
        if not row:
            self.error_msg = "用户不存在"
            return None
        if row["password_hash"] != hash_password(password):
            self.error_msg = "密码错误"
            return None
        if row["status"] == 0:
            self.error_msg = "账号已被禁用"
            return None
        return User(row["id"], row["username"], row["role"] or "user", row["phone_encrypted"])

    # ---------- 查询 ----------

    def get_user_by_username(self, username):
        with _conn() as conn:
            row = conn.execute(
                "SELECT id, username, phone_encrypted, role FROM users WHERE username = ?",
                (username,),
            ).fetchone()
        if not row:
            return None
        return User(row["id"], row["username"], row["role"] or "user", row["phone_encrypted"])

    def get_user_by_id(self, user_id):
        with _conn() as conn:
            row = conn.execute(
                "SELECT id, username, phone_encrypted, role FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        if not row:
            return None
        return User(row["id"], row["username"], row["role"] or "user", row["phone_encrypted"])

    def get_role(self, username):
        with _conn() as conn:
            row = conn.execute("SELECT role FROM users WHERE username = ?", (username,)).fetchone()
        return (row["role"] if row else None) or "user"

    def update_user_phone(self, username, encrypted_phone, new_phone_plain):
        try:
            with _conn() as conn:
                cur = conn.execute(
                    "UPDATE users SET phone = ?, phone_encrypted = ? WHERE username = ?",
                    (new_phone_plain, encrypted_phone, username),
                )
                n = cur.rowcount
            return n > 0
        except Exception:
            return False

    # ---------- 角色 / 用户管理（管理员） ----------

    def list_users(self, role=None):
        sql = "SELECT id, username, role, status, phone FROM users"
        params = []
        if role:
            sql += " WHERE role = ?"
            params.append(role)
        sql += " ORDER BY id ASC"
        with _conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def change_role(self, user_id, role):
        if role not in VALID_ROLES:
            return False, f"非法角色，允许值: {', '.join(VALID_ROLES)}"
        with _conn() as conn:
            cur = conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
        return cur.rowcount > 0, ""

    def set_user_status(self, user_id, status):
        status = 1 if status else 0
        with _conn() as conn:
            cur = conn.execute("UPDATE users SET status = ? WHERE id = ?", (status, user_id))
        return cur.rowcount > 0

    def reset_password(self, user_id, new_password):
        with _conn() as conn:
            cur = conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (hash_password(new_password), user_id),
            )
        return cur.rowcount > 0

    # ---------- TOTP 状态 ----------

    def is_totp_enabled(self, username):
        with _conn() as conn:
            row = conn.execute(
                "SELECT totp_enabled FROM users WHERE username = ?", (username,)
            ).fetchone()
        return bool(row and row["totp_enabled"])

    def get_totp_secret(self, username):
        with _conn() as conn:
            row = conn.execute(
                "SELECT totp_secret FROM users WHERE username = ?", (username,)
            ).fetchone()
        return row["totp_secret"] if row else None

    def save_totp_secret(self, username, secret):
        """绑定初始化：仅保存密钥，尚未启用。"""
        with _conn() as conn:
            cur = conn.execute(
                "UPDATE users SET totp_secret = ? WHERE username = ?", (secret, username)
            )
        return cur.rowcount > 0

    def enable_totp(self, username, recovery_hashes, counter):
        """确认绑定：启用 TOTP，写入恢复码哈希与初始计数器。"""
        with _conn() as conn:
            cur = conn.execute(
                """
                UPDATE users SET totp_enabled = 1, totp_bound_at = datetime('now','localtime'),
                       recovery_codes = ?, last_totp_counter = ?
                WHERE username = ?
                """,
                (json.dumps(recovery_hashes), counter, username),
            )
        return cur.rowcount > 0

    def disable_totp(self, username):
        with _conn() as conn:
            cur = conn.execute(
                """
                UPDATE users SET totp_enabled = 0, totp_secret = NULL,
                       recovery_codes = NULL, last_totp_counter = 0
                WHERE username = ?
                """,
                (username,),
            )
        return cur.rowcount > 0

    def reset_totp(self, username):
        """管理员代重置（设备丢失且无恢复码时的兜底，仅管理员可调用）。"""
        return self.disable_totp(username)

    # ---------- 防重放计数器 ----------

    def get_last_totp_counter(self, username):
        with _conn() as conn:
            row = conn.execute(
                "SELECT last_totp_counter FROM users WHERE username = ?", (username,)
            ).fetchone()
        return (row["last_totp_counter"] if row else None) or 0

    def set_last_totp_counter(self, username, counter):
        with _conn() as conn:
            cur = conn.execute(
                "UPDATE users SET last_totp_counter = ? WHERE username = ?", (counter, username)
            )
        return cur.rowcount > 0

    # ---------- 恢复码 ----------

    def get_recovery_hashes(self, username):
        with _conn() as conn:
            row = conn.execute(
                "SELECT recovery_codes FROM users WHERE username = ?", (username,)
            ).fetchone()
        if not row or not row["recovery_codes"]:
            return []
        try:
            return json.loads(row["recovery_codes"])
        except Exception:
            return []

    def consume_recovery_code(self, username, code_hash):
        """消费一次性恢复码：命中则移除并返回 True。"""
        with _conn() as conn:
            row = conn.execute(
                "SELECT recovery_codes FROM users WHERE username = ?", (username,)
            ).fetchone()
            if not row or not row["recovery_codes"]:
                return False
            try:
                hashes = json.loads(row["recovery_codes"])
            except Exception:
                return False
            if code_hash not in hashes:
                return False
            hashes.remove(code_hash)
            conn.execute(
                "UPDATE users SET recovery_codes = ? WHERE username = ?",
                (json.dumps(hashes), username),
            )
            return True


user_service = UserService()
