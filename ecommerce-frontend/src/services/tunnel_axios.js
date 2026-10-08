import axios from 'axios';
import { sealSecureRequest } from '../utils/secure_tunnel';

/** Shared by the ecommerce HTTP service and the standalone Week 4 demo. */
export function installSecureTunnelInterceptors(client) {
  client.interceptors.request.use(async config => {
    if (!config.secureTunnel) return config;
    try {
      const base = new URL(config.baseURL || '/', globalThis.location?.origin || 'http://127.0.0.1');
      const url = new URL(config.url, base);
      if (url.origin !== base.origin || url.search || url.hash || url.pathname !== '/api/v1/tunnel/echo' || config.method?.toUpperCase() !== 'POST') {
        throw new Error('安全隧道仅允许白名单 POST 接口，禁止查询参数');
      }
      if (config.__tunnelContext) throw new Error('不能自动重试已封装请求');
      config.skipAuthRefresh = true;
      const publicConfig = (await axios.get(new URL('/api/v1/tunnel/config', url).href, { timeout: 10000 })).data.data;
      const context = await sealSecureRequest(config.data, { method: config.method, path: url.pathname, config: publicConfig });
      config.__tunnelContext = context;
      config.data = context.envelope;
      config.headers['X-Secure-Tunnel'] = 'v2';
      return config;
    } catch (error) {
      error.config = config;
      throw error;
    }
  });
  client.interceptors.response.use(response => {
    const context = response.config.__tunnelContext;
    if (!response.config.secureTunnel) return response;
    try {
      if (!context) throw new Error('缺少响应解密上下文');
      const wire = { request: context.envelope, response: response.data, status: response.status };
      response.data = { ...response.data, data: context.openResponse(response.data?.data, response.status) };
      // Demo observer receives encrypted wire objects only, never key material.
      response.config.onSecureTunnelWire?.(wire);
      return response;
    } finally {
      context?.dispose();
      delete response.config.__tunnelContext;
    }
  }, error => {
    error.config?.__tunnelContext?.dispose();
    if (error.config) delete error.config.__tunnelContext;
    return Promise.reject(error);
  });
}
