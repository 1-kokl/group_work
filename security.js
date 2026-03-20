// 修改点2：修复导入路径 - 从 './sm_crypto' 改为 './sm_crypto.js'
// 1. 移除循环导入（核心修复点）
// import { checkPassword, checkUsername, checkPhone, hashPassword } from '../../utils/security'

// 2. 可选：如需启用SM加密，取消注释并确保sm_crypto.js存在
import { sm3Hash, sm4Encrypt, SM4_TEST_KEY } from './sm_crypto.js';

/**
 * 用户名校验
 * @param {string} username
 * @returns {Object} { valid: boolean, feedback: string[], score?: number } 统一返回对象格式
 */
export function checkUsername(username) {
  const feedback = [];
  let valid = true;

  if (!username) {
    valid = false;
    feedback.push('用户名不能为空');
  } else if (username.length < 4 || username.length > 20) {
    valid = false;
    feedback.push('用户名长度需4-20位');
  } else if (!/^[a-zA-Z0-9]+$/.test(username)) {
    valid = false;
    feedback.push('用户名仅支持字母和数字');
  }

  return { valid, feedback };
}

/**
 * 密码强度校验（增加score字段，适配前端强度展示）
 * @param {string} password
 * @returns {Object} { valid: boolean, feedback: string[], score: number }
 */
export function checkPassword(password) {
  const feedback = [];
  let valid = true;
  let score = 0; // 强度分：0-5，适配前端5段强度条

  if (!password) {
    valid = false;
    feedback.push('密码不能为空');
  } else {
    // 基础长度分
    if (password.length >= 8) score += 1;
    if (password.length >= 12) score += 1;
    // 字符类型分
    if (/[A-Z]/.test(password)) score += 1;
    if (/[0-9]/.test(password)) score += 1;
    // 特殊字符加分（可选，增强强度）
    if (/[^a-zA-Z0-9]/.test(password)) score += 1;

    // 校验规则
    if (password.length < 8) {
      valid = false;
      feedback.push('密码长度至少8位');
    }
    if (!/[A-Z]/.test(password)) {
      valid = false;
      feedback.push('密码需包含大写字母');
    }
    if (!/[0-9]/.test(password)) {
      valid = false;
      feedback.push('密码需包含数字');
    }
  }

  return { valid, feedback, score };
}

/**
 * 手机号校验
 * @param {string} phone
 * @returns {Object} { valid: boolean, feedback: string[] }
 */
export function checkPhone(phone) {
  const feedback = [];
  let valid = true;

  if (!phone) {
    valid = false;
    feedback.push('手机号不能为空');
  } else if (!/^1[3-9]\d{9}$/.test(phone)) {
    valid = false;
    feedback.push('手机号格式错误');
  }

  return { valid, feedback };
}

/**
 * 密码哈希（增加容错：未导入sm3时返回原密码，避免报错）
 * @param {string} password
 * @returns {string}
 */
export function hashPassword(password) {
  if (typeof sm3Hash === 'undefined') {
    console.warn('SM3哈希函数未导入，临时返回原密码（生产环境需修复）');
    return password;
  }
  return sm3Hash(password);
}

/**
 * 手机号加密（增加容错）
 * @param {string} phone
 * @returns {string}
 */
export function encryptPhone(phone) {
  if (typeof sm4Encrypt === 'undefined') {
    console.warn('SM4加密函数未导入，临时返回原手机号（生产环境需修复）');
    return phone;
  }
  return sm4Encrypt(phone, SM4_TEST_KEY);
}

/**
 * 输入清洗（防XSS）
 * @param {string} str
 * @returns {string}
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
