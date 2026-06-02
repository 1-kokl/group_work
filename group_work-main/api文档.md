# 用户认证 API 文档

## 文档访问地址



* 接口文档在线访问：`http://localhost:5000/docs/`

## 基础信息



* 基础 URL：`http://localhost:5000`

* 接口版本：v1

* 数据格式：JSON

* 认证方式：JWT（部分接口需要在请求头携带 `Authorization: Bearer {access_token}`）

## 统一响应格式

所有接口返回数据格式统一为：



```
{

&#x20; "code": 状态码,

&#x20; "msg": "提示信息",

&#x20; "timestamp": "响应时间（YYYY-MM-DD HH:MM:SS）",

&#x20; "data": 业务数据（可选）

}
```

## 一、用户管理接口（/api/v1）

### 1. 用户注册



* **路径**：`/api/v1/users`

* **方法**：POST

* **描述**：创建新用户账号

* **请求体**：



```
{

&#x20; "username": "test\_user",  // 用户名（6-20位，仅含字母、数字、下划线）

&#x20; "password": "Test@123",   // 密码（≥8位，含大小写字母、数字、特殊字符）

&#x20; "phone": "13800138000"    // 手机号（11位数字，13-9开头）

}
```



* **响应示例**：


  * 成功（201）：



```
{

&#x20; "code": 201,

&#x20; "msg": "注册成功",

&#x20; "timestamp": "2023-10-01 12:00:00",

&#x20; "data": {"username": "test\_user"}

}
```



* 失败（400）：



```
{

&#x20; "code": 400,

&#x20; "msg": "用户名已存在",

&#x20; "timestamp": "2023-10-01 12:00:00"

}
```

### 2. 获取当前用户信息



* **路径**：`/api/v1/users/me`

* **方法**：GET

* **描述**：获取登录用户的基本信息（需认证）

* **请求头**：`Authorization: Bearer {access_token}`

* **响应示例**：


  * 成功（200）：



```
{

&#x20; "code": 200,

&#x20; "msg": "查询成功",

&#x20; "timestamp": "2023-10-01 12:00:00",

&#x20; "data": {

&#x20;   "username": "test\_user",

&#x20;   "role": "buyer",

&#x20;   "phone\_encrypted": "MIIBIjANBgkqhkiG9w0BAQEF...（部分加密内容）"

&#x20; }

}
```



* 失败（404）：



```
{

&#x20; "code": 404,

&#x20; "msg": "用户不存在",

&#x20; "timestamp": "2023-10-01 12:00:00"

}
```

### 3. 更新用户手机号



* **路径**：`/api/v1/users/me/phone`

* **方法**：PATCH

* **描述**：修改当前登录用户的手机号（需认证）

* **请求头**：`Authorization: Bearer {access_token}`

* **请求体**：



```
{

&#x20; "phone": "13900139000"  // 新手机号（11位数字，13-9开头）

}
```



* **响应示例**：


  * 成功（200）：



```
{

&#x20; "code": 200,

&#x20; "msg": "手机号更新成功",

&#x20; "timestamp": "2023-10-01 12:00:00"

}
```



* 失败（400）：



```
{

&#x20; "code": 400,

&#x20; "msg": "手机号格式错误（11位数字）",

&#x20; "timestamp": "2023-10-01 12:00:00"

}
```

## 二、认证接口（/api/v1/auth）

### 1. 用户登录



* **路径**：`/api/v1/auth/login`

* **方法**：POST

* **描述**：用户登录并获取访问令牌

* **请求体**：



```
{

&#x20; "username": "test\_user",

&#x20; "password": "Test@123"

}
```



* **响应示例**：


  * 成功（200）：



```
{

&#x20; "code": 200,

&#x20; "msg": "登录成功",

&#x20; "timestamp": "2023-10-01 12:00:00",

&#x20; "data": {

&#x20;   "access\_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",  // 访问令牌（2小时有效）

&#x20;   "refresh\_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."  // 刷新令牌（7天有效）

&#x20; }

}
```



* 失败（401）：



```
{

&#x20; "code": 401,

&#x20; "msg": "密码错误，剩余3次",

&#x20; "timestamp": "2023-10-01 12:00:00"

}
```

### 2. 刷新访问令牌



* **路径**：`/api/v1/auth/refresh`

* **方法**：POST

* **描述**：使用刷新令牌获取新的访问令牌

* **请求体**：



```
{

&#x20; "refresh\_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."

}
```



* **响应示例**：


  * 成功（200）：



```
{

&#x20; "code": 200,

&#x20; "msg": "令牌刷新成功",

&#x20; "timestamp": "2023-10-01 12:00:00",

&#x20; "data": {

&#x20;   "access\_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."  // 新访问令牌

&#x20; }

}
```



* 失败（401）：



```
{

&#x20; "code": 401,

&#x20; "msg": "refresh\_token无效或已过期，请重新登录",

&#x20; "timestamp": "2023-10-01 12:00:00"

}
```

### 3. 注销登录



* **路径**：`/api/v1/auth/logout`

* **方法**：POST

* **描述**：注销当前登录状态（使访问令牌失效）

* **请求头**：`Authorization: Bearer {access_token}`

* **响应示例**：



```
{

&#x20; "code": 200,

&#x20; "msg": "注销成功",

&#x20; "timestamp": "2023-10-01 12:00:00"

}
```

## 错误码说明



| 状态码 | 说明             |
| --- | -------------- |
| 200 | 操作成功           |
| 201 | 资源创建成功         |
| 400 | 请求参数错误         |
| 401 | 未认证（令牌无效 / 过期） |
| 404 | 资源不存在          |
| 500 | 服务器内部错误        |
