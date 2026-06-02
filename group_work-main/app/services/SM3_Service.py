from gmssl.sm3 import sm3_hash as _gmssl_sm3_hash, bytes_to_list


def sm3_hash(data):
    """
    SM3 哈希（替代 SHA256）
    :param data: 字符串或字节串
    :return: 64 位十六进制小写字符串
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    elif not isinstance(data, bytes):
        raise TypeError("输入数据仅支持字符串/字节串")
    return _gmssl_sm3_hash(bytes_to_list(data))


def hash_password(password):
    """密码哈希（SM3）"""
    return sm3_hash(password)


if __name__ == "__main__":
    test_pwd = "TestPass123!"
    print(f"原始密码: {test_pwd}")
    print(f"SM3哈希: {hash_password(test_pwd)}")
