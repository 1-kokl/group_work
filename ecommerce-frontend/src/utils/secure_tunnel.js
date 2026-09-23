import { sm2, sm4 } from 'sm-crypto-v2';

export const VERSION = 'v2';
export const ALGORITHM = 'SM4-GCM+SM2';
const encoder = new TextEncoder();
const decoder = new TextDecoder('utf-8', { fatal: true });
export const b64 = bytes => btoa(String.fromCharCode(...bytes));
const unb64 = text => {
  if (typeof text !== 'string') throw new Error('Invalid Base64');
  const bytes = Uint8Array.from(atob(text), c => c.charCodeAt(0));
  if (b64(bytes) !== text) throw new Error('Noncanonical Base64');
  return bytes;
};
const nonceBytes = text => {
  if (typeof text !== 'string' || !/^[A-Za-z0-9_-]{16}$/.test(text)) throw new Error('Invalid nonce');
  return unb64(text.replace(/-/g, '+').replace(/_/g, '/'));
};
const nonceText = bytes => b64(bytes).replace(/\+/g, '-').replace(/\//g, '_');
const hexBytes = hex => Uint8Array.from(hex.match(/../g), s => parseInt(s, 16));

function aad(env, method, path, direction, status = 200) {
  const parts = [VERSION, ALGORITHM, env.key_id, env.ts, env.nonce, method.toUpperCase(), path, direction];
  if (direction === 'response') parts.push(env.request_nonce, status);
  return encoder.encode(parts.join('|'));
}

export function isSecureTunnelEnvelope(value) {
  return Boolean(value && value.version === VERSION && value.alg === ALGORITHM && value.ciphertext && value.tag);
}

/** Private request key lives only in this closure, never in JSON, storage or callbacks. */
export async function sealSecureRequest(payload, { method, path, config, now = Math.floor(Date.now() / 1000) }) {
  if (method.toUpperCase() !== 'POST' || path !== '/api/v1/tunnel/echo') throw new Error('接口不在隧道白名单');
  if (!payload || Array.isArray(payload) || typeof payload !== 'object') throw new Error('正文必须是 JSON 对象');
  if (config.version !== VERSION || config.alg !== ALGORITHM || !/^sm2-[a-f0-9]{16}$/.test(config.key_id)) throw new Error('服务端协议不匹配');
  if (!/^[a-fA-F0-9]{128}$/.test(config.sm2_public_key) || !sm2.verifyPublicKey('04' + config.sm2_public_key)) throw new Error('SM2 公钥无效');
  const key = crypto.getRandomValues(new Uint8Array(16));
  const nonce = crypto.getRandomValues(new Uint8Array(12));
  const envelope = { version: VERSION, key_id: config.key_id, alg: ALGORITHM, nonce: nonceText(nonce), ts: now };
  let responseKey;
  let used = false;
  try {
    // C1(x||y) || C3 || C2, no 04 prefix; plaintext is the raw 16-byte key.
    envelope.wrapped_key = b64(hexBytes(sm2.doEncrypt(key, '04' + config.sm2_public_key, 1)));
    const encrypted = sm4.encrypt(encoder.encode(JSON.stringify(payload)), key, {
      mode: 'gcm',
      iv: nonce,
      associatedData: aad(envelope, method, path, 'request'),
      output: 'array',
      outputTag: true,
      padding: 'none'
    });
    envelope.ciphertext = b64(encrypted.output);
    envelope.tag = b64(encrypted.tag);
    const material = await crypto.subtle.importKey('raw', key, 'HKDF', false, ['deriveBits']);
    responseKey = new Uint8Array(await crypto.subtle.deriveBits({
      name: 'HKDF', hash: 'SHA-256', salt: nonce, info: encoder.encode('week4-v2-response')
    }, material, 128));
  } finally {
    key.fill(0);
  }
  const expected = { ...envelope };
  function dispose() { used = true; responseKey.fill(0); }
  function openResponse(env, status = 200) {
    if (used) throw new Error('响应上下文已使用或释放');
    try {
      const fields = ['version', 'key_id', 'alg', 'nonce', 'ts', 'request_nonce', 'ciphertext', 'tag'].sort();
      if (!env || JSON.stringify(Object.keys(env).sort()) !== JSON.stringify(fields) || !isSecureTunnelEnvelope(env)) throw new Error('响应信封格式错误');
      if (env.key_id !== expected.key_id || env.request_nonce !== expected.nonce) throw new Error('响应与请求不匹配');
      if (!Number.isSafeInteger(env.ts) || Math.abs(Math.floor(Date.now() / 1000) - env.ts) > 300) throw new Error('响应过期');
      const tag = unb64(env.tag);
      if (tag.length !== 16) throw new Error('响应标签长度错误');
      const decrypted = sm4.decrypt(unb64(env.ciphertext), responseKey, {
        mode: 'gcm',
        iv: nonceBytes(env.nonce),
        associatedData: aad(env, method, path, 'response', status),
        tag,
        output: 'array',
        padding: 'none'
      });
      const payload = JSON.parse(decoder.decode(decrypted));
      if (!payload || Array.isArray(payload) || typeof payload !== 'object') throw new Error('响应正文类型错误');
      return payload;
    } finally { dispose(); }
  }
  return { envelope, openResponse, dispose };
}
