/**
 * 应用层安全隧道的浏览器适配层。
 *
 * SM4-GCM 和 SM2 的具体实现通过运行时 crypto bridge 注入，避免把私钥、会话密钥
 * 写入 localStorage 或普通日志。bridge 需要实现：
 *   seal(payload, { method, path, config }) -> Promise<envelope>
 *   open(envelope, { method, path, config }) -> Promise<plainObject>
 *
 * 生产环境可由国密浏览器扩展、WebAssembly 国密库或经过评审的前端密码库提供 bridge。
 */
let cryptoBridge = null;

export function setSecureTunnelCrypto(bridge) {
  if (!bridge || typeof bridge.seal !== 'function' || typeof bridge.open !== 'function') {
    throw new TypeError('安全隧道 crypto bridge 必须实现 seal/open');
  }
  cryptoBridge = bridge;
}

export function hasSecureTunnelCrypto() {
  return Boolean(cryptoBridge);
}

export function isSecureTunnelEnvelope(value) {
  return Boolean(
    value &&
      value.version === 'v1' &&
      value.alg === 'SM4-GCM+SM2' &&
      value.nonce &&
      value.wrapped_key &&
      value.ciphertext &&
      value.tag
  );
}

export async function sealSecureRequest(payload, options) {
  if (!cryptoBridge) {
    throw new Error('未配置安全隧道 crypto bridge');
  }
  return cryptoBridge.seal(payload, options);
}

export async function openSecureResponse(envelope, options) {
  if (!cryptoBridge) {
    throw new Error('未配置安全隧道 crypto bridge');
  }
  return cryptoBridge.open(envelope, options);
}

