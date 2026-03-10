import gmssl
import hashlib


def sm3_hash(data):
    """
    SM3哈希算法实现（替代SHA256）
    :param data: 待哈希的字符串/字节串
    :return: SM3哈希结果（16进制字符串）
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    elif not isinstance(data, bytes):
        raise TypeError("输入数据仅支持字符串/字节串")

    sm3 = gmssl.sm3.SM3()
    sm3.update(data)
    return sm3.hexdigest()


# 兼容原hash_password函数名，无缝替换
def hash_password(password):
    """密码哈希（SM3）"""
    return sm3_hash(password)


# 测试函数（可选）
if __name__ == "__main__":
    test_pwd = "TestPass123!"
    print(f"原始密码: {test_pwd}")
    print(f"SM3哈希: {hash_password(test_pwd)}")