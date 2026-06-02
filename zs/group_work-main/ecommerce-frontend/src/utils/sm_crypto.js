import { sm3, sm4 } from 'sm-crypto';

/**
 * SM3哈希算法
 * @param {string} data 输入字符串
 * @returns {string} 哈希结果（十六进制字符串）
 */
export function sm3Hash(data) {
  if (!data) return '';
  return sm3(data);
}

/**
 * SM4加密
 * @param {string} data 要加密的数据
 * @param {string} key 加密密钥（十六进制字符串）
 * @returns {string} Base64编码的密文
 */
export function sm4Encrypt(data, key) {
  if (!data) return '';

  try {
    const encrypted = sm4.encrypt(data, key);
    return btoa(encrypted);
  } catch (error) {
    console.error('SM4加密失败:', error);
    return data;
  }
}

/**
 * SM4解密
 * @param {string} encryptedData Base64密文
 * @param {string} key 解密密钥（十六进制字符串）
 * @returns {string} 解密后的数据
 */
export function sm4Decrypt(encryptedData, key) {
  if (!encryptedData) return '';

  try {
    const encrypted = atob(encryptedData);
    return sm4.decrypt(encrypted, key);
  } catch (error) {
    console.error('SM4解密失败:', error);
    return encryptedData;
  }
}

/**
 * 测试用的SM4密钥（32位十六进制字符串）
 */
export const SM4_TEST_KEY = '0123456789abcdef0123456789abcdef';

export default {
  sm3Hash,
  sm4Encrypt,
  sm4Decrypt,
  SM4_TEST_KEY
};
