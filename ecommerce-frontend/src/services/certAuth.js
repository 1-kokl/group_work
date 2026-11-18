/**
 * 证书认证相关请求工具
 * 对接后端证书验证接口，支持证书签名、非对称加密等强认证逻辑
 */
import { getCsrfToken } from './http';
const API_BASE = process.env.VUE_APP_API_BASE_URL || 'http://localhost:5000';
/**
 * 携带证书信息发起认证请求
 * @param {Object} params - 证书认证参数
 * @returns {Promise<Object>} 认证结果（token/用户信息）
 */
export const requestWithCert = async (params) => {
  const csrfToken = getCsrfToken(); // 从cookie获取CSRF Token
  const response = await fetch(`${API_BASE}/api/v1/auth/cert-login`, {
    method: 'POST',
    // certAuth.js 中修正 Accept 请求头
    headers: {
      'Content-Type': 'application/json',
      'X-CSRF-Token': csrfToken,
      Accept: 'application/json' // 去掉多余引号
    },
    body: JSON.stringify({
      ...params,
      // 可选：添加前端签名（使用证书私钥签名，后端验签）
      signature: await signWithCertPrivateKey(params.nonce)
    })
  });

  const result = await response.json();

  if (!response.ok) {
    throw new Error(result.message || `证书认证失败（${response.status}）`);
  }

  return result.data;
};

/**
 * 模拟使用证书私钥签名（实际需对接WebCrypto API/证书插件）
 * @param {string} data - 待签名数据
 * @returns {Promise<string>} 签名结果
 */
export const signWithCertPrivateKey = async (data) => {
  // 生产环境：调用证书插件提供的签名接口
  // 示例：return await window.certPlugin.sign(data, selectedCert.thumbprint);
  return btoa(data + '-mock-signature'); // 模拟签名
};

