import { sm3Hash, sm4Encrypt, SM4_TEST_KEY } from './sm_crypto';

/**
 * 用户名校验（保留原逻辑）
 * @param {string} username 
 * @returns {[boolean, string]} [是否有效, 提示信息]
 */
export function checkUsername(username) {
  if (!username) return [false, '用户名不能为空'];
  if (username.length < 4 || username.length > 20) {
    return [false, '用户名长度需4-20位'];
  }
  if (!/^[a-zA-Z0-9]+$/.test(username)) {
    return [false, '用户名仅支持字母和数字'];
  }
  return [true, ''];
}

/**
 * 密码强度校验（保留原逻辑）
 * @param {string} password 
 * @returns {[boolean, string]}
 */
export function checkPassword(password) {
  if (!password) return [false, '密码不能为空'];
  if (password.length < 8) {
    return [false, '密码长度至少8位'];
  }
  if (!/[A-Z]/.test(password)) {
    return [false, '密码需包含大写字母'];
  }
  if (!/[0-9]/.test(password)) {
    return [false, '密码需包含数字'];
  }
  return [true, ''];
}

/**
 * 手机号校验（保留原逻辑）
 * @param {string} phone 
 * @returns {[boolean, string]}
 */
export function checkPhone(phone) {
  if (!phone) return [false, '手机号不能为空'];
  if (!/^1[3-9]\d{9}$/.test(phone)) {
    return [false, '手机号格式错误'];
  }
  return [true, ''];
}

/**
 * 密码哈希（SM3替代SHA256）
 * @param {string} password 
 * @returns {string} SM3哈希结果
 */
export function hashPassword(password) {
  return sm3Hash(password);
}

/**
 * 手机号加密（前端SM4，对齐后端）
 * @param {string} phone 
 * @returns {string} Base64密文
 */
export function encryptPhone(phone) {
  return sm4Encrypt(phone, SM4_TEST_KEY);
}

/**
 * 输入清洗（防XSS，保留原逻辑）
 * @param {string} str 
 * @returns {string} 清洗后的字符串
 */
export function sanitizeInput(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}