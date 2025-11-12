# 在导入部分添加
from flask_swagger_ui import get_swaggerui_blueprint
import yaml

# ========== Swagger配置 ==========
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.yaml'

# 初始化Swagger
swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "电子商务系统API文档",
        'docExpansion': 'none',
        'persistAuthorization': True
    }
)


def create_swagger_spec():
    """生成Swagger规范"""
    swagger_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "电子商务系统RESTful API",
            "description": "基于Flask开发的电子商务系统API接口文档",
            "version": "1.0.0",
            "contact": {
                "name": "API支持",
                "email": "support@example.com"
            }
        },
        "servers": [
            {
                "url": "http://localhost:5000",
                "description": "开发服务器"
            }
        ],
        "paths": {
            "/api/v1/user/register": {
                "post": {
                    "summary": "用户注册",
                    "description": "注册新用户账户",
                    "tags": ["用户管理"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["username", "password", "phone"],
                                    "properties": {
                                        "username": {
                                            "type": "string",
                                            "description": "用户名（6-20位字母数字下划线）",
                                            "example": "testuser123"
                                        },
                                        "password": {
                                            "type": "string",
                                            "description": "密码（8位以上，含大小写数字特殊字符）",
                                            "example": "SecurePass123!"
                                        },
                                        "phone": {
                                            "type": "string",
                                            "description": "手机号（11位数字）",
                                            "example": "13812345678"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "注册成功",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "code": 200,
                                        "msg": "✅ 注册成功",
                                        "data": None
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "请求参数错误",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "code": 400,
                                        "msg": "❌❌ 用户名已存在",
                                        "data": None
                                    }
                                }
                            }
                        },
                        "429": {
                            "description": "请求频率过高"
                        }
                    }
                }
            },
            "/api/v1/user/login": {
                "post": {
                    "summary": "用户登录",
                    "description": "用户登录获取JWT令牌",
                    "tags": ["认证管理"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["username", "password"],
                                    "properties": {
                                        "username": {"type": "string", "example": "testuser123"},
                                        "password": {"type": "string", "example": "SecurePass123!"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "登录成功",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "code": 200,
                                        "msg": "✅ 登录成功",
                                        "data": {
                                            "access_token": "eyJ0eXAiOiJKV1Qi...",
                                            "role": "buyer"
                                        }
                                    }
                                }
                            }
                        },
                        "401": {
                            "description": "认证失败"
                        }
                    }
                }
            },
            "/api/v1/user/info": {
                "get": {
                    "summary": "获取用户信息",
                    "description": "获取当前登录用户的基本信息",
                    "tags": ["用户管理"],
                    "security": [{"BearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "获取成功",
                            "content": {
                                "application/json": {
                                    "example": {
                                        "code": 200,
                                        "msg": "✅ 获取成功",
                                        "data": {
                                            "username": "testuser123",
                                            "role": "buyer",
                                            "phone": "138****5678"
                                        }
                                    }
                                }
                            }
                        },
                        "401": {
                            "description": "未授权访问"
                        }
                    }
                }
            }
        },
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            }
        }
    }

    # 保存Swagger文档
    os.makedirs('static', exist_ok=True)
    with open('static/swagger.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(swagger_spec, f, allow_unicode=True, default_flow_style=False)