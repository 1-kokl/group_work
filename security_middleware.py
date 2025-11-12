# security_middleware.py
import re
import time
import redis
from functools import wraps
from flask import request, jsonify


class RateLimiter:
    def __init__(self, max_requests=100, window=900):
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            self.redis_client.ping()  # 测试连接
        except redis.ConnectionError:
            self.redis_client = None  # Redis不可用时不启用限制
        self.max_requests = max_requests
        self.window = window

    def is_rate_limited(self, key):
        if not self.redis_client:
            return False  # Redis不可用时不限制

        try:
            current = int(time.time())
            window_start = current - self.window

            # 移除过期记录
            self.redis_client.zremrangebyscore(key, 0, window_start)

            # 获取当前窗口内的请求数
            request_count = self.redis_client.zcard(key)

            if request_count >= self.max_requests:
                return True

            # 添加新请求
            self.redis_client.zadd(key, {str(current): current})
            self.redis_client.expire(key, self.window)
            return False
        except Exception:
            return False


rate_limiter = RateLimiter()


def limit_rate(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr
        if rate_limiter.is_rate_limited(f"rate_limit:{client_ip}"):
            return jsonify({
                "code": 429,
                "msg": "❌ 请求过于频繁，请稍后再试"
            }), 429
        return f(*args, **kwargs)

    return decorated_function


def validate_input(required_fields=None, field_rules=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if required_fields:
                data = request.get_json() or {}
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        "code": 400,
                        "msg": f"❌ 缺少必填字段: {', '.join(missing_fields)}"
                    }), 400

            if field_rules:
                data = request.get_json() or {}
                for field, rule in field_rules.items():
                    if field in data:
                        value = data[field]
                        if 'type' in rule and not isinstance(value, rule['type']):
                            return jsonify({
                                "code": 400,
                                "msg": f"❌ 字段 {field} 类型错误"
                            }), 400
                        if 'min_length' in rule and len(str(value)) < rule['min_length']:
                            return jsonify({
                                "code": 400,
                                "msg": f"❌ 字段 {field} 长度不能少于 {rule['min_length']} 个字符"
                            }), 400
                        if 'max_length' in rule and len(str(value)) > rule['max_length']:
                            return jsonify({
                                "code": 400,
                                "msg": f"❌ 字段 {field} 长度不能超过 {rule['max_length']} 个字符"
                            }), 400

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def sanitize_input(data):
    if isinstance(data, str):
        dangerous_patterns = [
            r'(\bUNION\b|\bSELECT\b|\bINSERT\b|\bDELETE\b|\bUPDATE\b|\bDROP\b|\bEXEC\b)',
            r'(\-\-|\#|\/\*)',
            r'(\bOR\b.*=.*)'
        ]
        for pattern in dangerous_patterns:
            data = re.sub(pattern, '', data, flags=re.IGNORECASE)
    return data


def escape_html(text):
    if not text:
        return text
    escape_chars = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '/': '&#x2F;'
    }
    for char, escape in escape_chars.items():
        text = text.replace(char, escape)
    return text


def setup_security_headers(app):
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        return response

    return app