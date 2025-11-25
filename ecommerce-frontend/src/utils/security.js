/**
 * HTML 实体映射表，用于将特殊字符转换为安全的文本表示
 */
const HTML_ESCAPE_MAP = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
  '`': '&#96;'
};

/**
 * 将潜在危险的 HTML 字符进行转义
 * @param {string} value 待转义的字符串
 * @returns {string} 已转义的安全字符串
 */
export function escapeHTML(value = '') {
  return String(value).replace(/[&<>"'`]/g, (match) => HTML_ESCAPE_MAP[match]);
}

/**
 * 基础的 XSS 输入过滤
 * - 去除 script、style、iframe 标签
 * - 移除内联事件（例如 onclick）
 * - 对剩余文本进行 HTML 转义
 * @param {string} value 用户输入的原始字符串
 * @returns {string} 过滤后的安全字符串
 */
export function sanitizeInput(value = '') {
  return escapeHTML(
    String(value)
      .replace(/<(script|style|iframe)[^>]*>.*?<\/\1>/gi, '')
      .replace(/\son\w+="[^"]*"/gi, '')
      .replace(/\son\w+='[^']*'/gi, '')
  );
}

/**
 * 通用表单校验器
 * @param {Record<string, any>} fields 待校验的字段对象
 * @param {Record<string, Function>} validators 与字段对应的校验函数
 * @returns {{ valid: boolean; errors: Record<string, string> }}
 */
export function validateForm(fields, validators) {
  const errors = {};
  Object.entries(validators || {}).forEach(([key, validator]) => {
    if (typeof validator !== 'function') return;

    const result = validator(fields?.[key]);

    if (result !== true) {
      errors[key] = typeof result === 'string' ? result : '请输入有效的内容';
    }
  });

  return {
    valid: Object.keys(errors).length === 0,
    errors
  };
}

/**
 * 密码强度验证
 * - 至少 8 位
 * - 同时包含大写、小写、数字、特殊字符中的任意三种
 * @param {string} password 密码原文
 * @returns {{ valid: boolean; score: number; feedback: string[] }}
 */
export function validatePasswordStrength(password = '') {
  const feedback = [];
  const checks = {
    length: password.length >= 8,
    upper: /[A-Z]/.test(password),
    lower: /[a-z]/.test(password),
    number: /\d/.test(password),
    special: /[!@#$%^&*()]/.test(password)
  };

  if (!checks.length) feedback.push('密码长度至少 8 位。');
  if (!checks.upper) feedback.push('需包含大写字母。');
  if (!checks.lower) feedback.push('需包含小写字母。');
  if (!checks.number) feedback.push('需包含数字。');
  if (!checks.special) feedback.push('需包含特殊符号 !@#$%^&*() 中至少一个。');

  const score = Object.values(checks).filter(Boolean).length;
  const valid =
    checks.length &&
    checks.upper &&
    checks.lower &&
    checks.number &&
    checks.special;

  return {
    valid,
    score,
    feedback
  };
}

/**
 * 国内手机号格式校验（中国大陆）
 * @param {string} phone 手机号
 * @returns {true|string} true 表示通过，其余返回错误提示
 */
export function validatePhoneNumber(phone = '') {
  if (!/^1[3-9]\d{9}$/.test(phone)) {
    return '请输入正确的 11 位手机号。';
  }
  return true;
}

/**
 * 用户名格式校验
 * - 以字母开头
 * - 允许数字与下划线
 * - 长度 4-18 位
 * @param {string} username 用户名
 * @returns {true|string} true 表示通过，其余返回错误提示
 */
export function validateUsername(username = '') {
  if (!/^[A-Za-z0-9_]{6,20}$/.test(username)) {
    return '用户名需为 6-20 位的字母、数字或下划线组合。';
  }
  return true;
}

