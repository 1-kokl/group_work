"""
审计日志服务。

在 user.db 中维护 audit_logs 表，记录「谁在什么时候对什么对象做了什么、结果如何」，
支撑任务书验收要点「管理员关键操作可追溯」。

事件动作统一用大写常量（见 docs/03_审计事件字典.md），result 取值：
    success / denied / failure
"""
import json
import os
import sqlite3
from datetime import datetime

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
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                user_id INTEGER,
                username TEXT,
                role TEXT,
                action TEXT NOT NULL,
                resource TEXT,
                resource_id TEXT,
                result TEXT NOT NULL DEFAULT 'success',
                ip TEXT,
                detail TEXT
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_logs(ts)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action)"
        )


# 模块加载时确保表存在
_ensure_table()


def write_log(user_id=None, username=None, role=None, action="", resource=None,
              resource_id=None, result="success", ip=None, detail=""):
    """写入一条审计日志。"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with _conn() as conn:
            conn.execute(
                """
                INSERT INTO audit_logs
                (ts, user_id, username, role, action, resource, resource_id, result, ip, detail)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (ts, user_id, username, role, action, resource, resource_id,
                 result, ip, detail),
            )
    except Exception as e:
        print(f"[AUDIT] 写日志失败: {e}")


def query_logs(action=None, username=None, result=None, start=None, end=None,
               limit=100, offset=0):
    """查询审计日志，供审计员/管理员查看。"""
    sql = "SELECT * FROM audit_logs WHERE 1=1"
    params = []
    if action:
        sql += " AND action = ?"
        params.append(action)
    if username:
        sql += " AND username = ?"
        params.append(username)
    if result:
        sql += " AND result = ?"
        params.append(result)
    if start:
        sql += " AND ts >= ?"
        params.append(start)
    if end:
        sql += " AND ts <= ?"
        params.append(end)
    sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([int(limit), int(offset)])

    with _conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def count_logs(action=None, username=None, result=None):
    """统计日志条数。"""
    sql = "SELECT COUNT(*) AS n FROM audit_logs WHERE 1=1"
    params = []
    if action:
        sql += " AND action = ?"
        params.append(action)
    if username:
        sql += " AND username = ?"
        params.append(username)
    if result:
        sql += " AND result = ?"
        params.append(result)
    with _conn() as conn:
        return conn.execute(sql, params).fetchone()["n"]


if __name__ == "__main__":
    write_log(username="admin", role="admin", action="USER_ROLE_CHANGE",
              resource="user", resource_id="2", result="success", detail="test")
    print(json.dumps(query_logs(limit=3), ensure_ascii=False, indent=2))
