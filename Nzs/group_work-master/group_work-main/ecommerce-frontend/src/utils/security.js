// 修改点2：修复导入路径 - 从 './sm_crypto' 改为 './sm_crypto.js'
import { sm3Hash, sm4Encrypt, SM4_TEST_KEY } from './sm_crypto.js';

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
} // 修改点3：删除了第5行末尾的空格

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
} // 修改点4：删除了第21行末尾的空格

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
} // 修改点5：删除了第40行末尾的空格

/**
 * 密码哈希（SM3替代SHA256）
 * @param {string} password
 * @returns {string} SM3哈希结果
 */
export function hashPassword(password) {
  return sm3Hash(password);
} // 修改点6：删除了第53行末尾的空格

/**
 * 手机号加密（前端SM4，对齐后端）
 * @param {string} phone
 * @returns {string} Base64密文
 */
export function encryptPhone(phone) {
  return sm4Encrypt(phone, SM4_TEST_KEY);
} // 修改点7：删除了第62行末尾的空格

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

/** @returns {true|string} */
export function validateUsername(username) {
  const [ok, msg] = checkUsername(username);
  return ok ? true : msg;
}

/** @returns {true|string} */
export function validatePhoneNumber(phone) {
  const [ok, msg] = checkPhone(phone);
  return ok ? true : msg;
}

/**
 * 供注册页强度条与校验使用
 * @returns {{ valid: boolean, feedback: string[], score: number }}
 */
export function validatePasswordStrength(password) {
  const feedback = [];
  let score = 0;
  if (!password) {
    return { valid: false, feedback: ['密码不能为空'], score: 0 };
  }
  if (password.length >= 8) score += 1;
  if (password.length >= 12) score += 1;
  if (/[A-Z]/.test(password)) score += 1;
  if (/[0-9]/.test(password)) score += 1;
  if (/[^a-zA-Z0-9]/.test(password)) score += 1;

  const [ok, msg] = checkPassword(password);
  if (!ok) {
    feedback.push(msg);
  }
  return { valid: ok, feedback, score };
}

