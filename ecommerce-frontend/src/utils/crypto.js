/**
 * 前端生成RSA密钥对 + CSR（证书签名请求）
 * 基于Web Crypto API，仅支持HTTPS/localhost环境
 */
import { ElMessage } from 'element-plus';

// 根证书下载（假设根证书文件放在public/certs/rootCA.pem）
export const downloadRootCert = () => {
  const link = document.createElement('a');
  link.href = '/certs/rootCA.pem'; // 根证书存放路径
  link.download = 'ecommerce-root-ca.pem';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  ElMessage.success('根证书下载成功');
};

// 生成RSA密钥对（2048位）
export const generateRSAKeyPair = async () => {
  try {
    const keyPair = await window.crypto.subtle.generateKey(
      {
        name: 'RSASSA-PKCS1-v1_5',
        modulusLength: 2048,
        publicExponent: new Uint8Array([0x01, 0x00, 0x01]),
        hash: { name: 'SHA-256' }
      },
      true, // 可导出
      ['sign', 'verify']
    );
    return keyPair;
  } catch (error) {
    ElMessage.error('密钥对生成失败：' + error.message);
    throw error;
  }
};

// 导出公钥为PEM格式
export const exportPublicKeyToPEM = async (publicKey) => {
  const exported = await window.crypto.subtle.exportKey('spki', publicKey);
  const pem = arrayBufferToPEM(exported, 'PUBLIC KEY');
  return pem;
};

// 导出私钥为PEM格式（注意：前端仅临时存储，生产环境需谨慎）
export const exportPrivateKeyToPEM = async (privateKey) => {
  const exported = await window.crypto.subtle.exportKey('pkcs8', privateKey);
  const pem = arrayBufferToPEM(exported, 'PRIVATE KEY');
  return pem;
};

// 生成CSR（简化版，仅核心字段）
export const generateCSR = async (keyPair, subject) => {
  try {
    // 简化版CSR生成（生产环境建议用成熟库如pkijs）
    const publicKeyPem = await exportPublicKeyToPEM(keyPair.publicKey);
    const csrContent = `-----BEGIN CERTIFICATE REQUEST-----
${btoa(JSON.stringify({
  subject: subject, // { CN: 'example.com', O: 'Ecommerce', C: 'CN' }
  publicKey: publicKeyPem,
  signatureAlgorithm: 'sha256WithRSAEncryption',
  timestamp: new Date().toISOString()
}))}
-----END CERTIFICATE REQUEST-----`;
    return csrContent;
  } catch (error) {
    ElMessage.error('CSR生成失败：' + error.message);
    throw error;
  }
};

// 下载CSR文件
export const downloadCSR = (csrContent, filename = 'cert-request.csr') => {
  const blob = new Blob([csrContent], { type: 'application/pkcs10' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(link.href);
  ElMessage.success('CSR文件已下载');
};

// 辅助函数：ArrayBuffer转PEM格式
const arrayBufferToPEM = (ab, type) => {
  const base64 = btoa(String.fromCharCode(...new Uint8Array(ab)));
  const lines = [];
  lines.push(`-----BEGIN ${type}-----`);
  // 按64字符拆分
  for (let i = 0; i < base64.length; i += 64) {
    lines.push(base64.substring(i, i + 64));
  }
  lines.push(`-----END ${type}-----`);
  return lines.join('\n');
};

