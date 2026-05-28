import axios from 'axios';

/* 开发环境可置空字符串，走 vue.config 代理；直连后端时设为 http://localhost:5000 */
const API_BASE_URL =
  process.env.VUE_APP_API_BASE_URL !== undefined
    ? process.env.VUE_APP_API_BASE_URL
    : '';

const TOKEN_KEY = 'auth.token';
const REFRESH_TOKEN_KEY = 'auth.refreshToken';
const EXPIRES_AT_KEY = 'auth.expiresAt';

const CSRF_HEADER = 'X-CSRF-Token';
const CSRF_STORAGE_KEY = 'auth.csrfToken';

const storage = typeof window !== 'undefined' ? window.sessionStorage : null;

const http = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  withCredentials: false,
  headers: {
    'Content-Type': 'application/json'
  }
});

let activeRequests = 0;
let isRefreshing = false;
let refreshPromise = null;
const refreshSubscribers = [];

const ERROR_CODE_MESSAGES = {
  AUTH_INVALID: '账号或密码错误。',
  AUTH_LOCKED: '账户已被锁定，请联系管理员。',
  AUTH_EXPIRED: '登录状态已过期，请重新登录。',
  VALIDATION_FAILED: '提交的数据验证失败，请检查后重试。',
  RATE_LIMIT: '请求过于频繁，请稍后再试。',
  SERVER_ERROR: '服务器开小差了，请稍后再试。'
};

function readCsrfFromCookie() {
  if (typeof document === 'undefined') return '';
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/i);
  return match ? decodeURIComponent(match[1]) : '';
}

function getCsrfToken() {
  const stored = storage?.getItem(CSRF_STORAGE_KEY);
  if (stored) return stored;
  const cookieToken = readCsrfFromCookie();
  if (cookieToken) {
    storage?.setItem(CSRF_STORAGE_KEY, cookieToken);
  }
  return cookieToken;
}

function setCsrfToken(token) {
  if (!token) return;
  try {
    storage?.setItem(CSRF_STORAGE_KEY, token);
  } catch (error) {
    console.warn('[HTTP] 存储 CSRF 令牌失败:', error);
  }
}

function clearCsrfToken() {
  storage?.removeItem(CSRF_STORAGE_KEY);
}

function emitLoadingEvent() {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(
    new CustomEvent('http:loading', {
      detail: activeRequests > 0
    })
  );
}

function emitErrorEvent(error) {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(
    new CustomEvent('http:error', {
      detail: error
    })
  );
}

function emitTokenEvent(detail, eventName = 'auth:token-refreshed') {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(new CustomEvent(eventName, { detail }));
}

function decrementRequest() {
  activeRequests = Math.max(activeRequests - 1, 0);
  emitLoadingEvent();
}

function normalizeHttpError(error, fallbackMessage = '请求失败，请稍后重试。') {
  if (axios.isCancel(error)) {
    const cancelled = new Error('请求已取消');
    cancelled.code = 'REQUEST_CANCELLED';
    cancelled.status = 0;
    return cancelled;
  }

  const status = error?.response?.status ?? 0;
  const code = error?.response?.data?.code ?? 'UNKNOWN';
  const resData = error?.response?.data;
  let message =
    resData?.message ||
    resData?.msg ||
    ERROR_CODE_MESSAGES[code] ||
    (status === 0
      ? '网络连接异常，请检查网络后重试。'
      : fallbackMessage);
  const details = resData?.errors || null;

  if (
    status === 401 &&
    typeof error?.config?.url === 'string' &&
    error.config.url.includes('/api/v1/auth/login')
  ) {
    message = '用户名或密码错误，请重试。';
  }

  const normalized = new Error(message);
  normalized.code = code;
  normalized.status = status;
  normalized.details = details;

  if (status >= 500 || status === 0) {
    console.error('[HTTP ERROR]', {
      status,
      code,
      message,
      details,
      url: error?.config?.url
    });
  }

  const suppressGlobalError =
    error?.config?.suppressGlobalError || error?.config?.suppressErrorEvent;

  if (!suppressGlobalError) {
    emitErrorEvent({
      ...normalized,
      message,
      code,
      status,
      details
    });
  }

  return normalized;
}

function writeTokens({ token, refreshToken, expiresAt }) {
  if (token) {
    storage?.setItem(TOKEN_KEY, token);
  }
  if (refreshToken) {
    storage?.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }
  if (expiresAt) {
    storage?.setItem(EXPIRES_AT_KEY, String(expiresAt));
  }
}

function clearTokens() {
  storage?.removeItem(TOKEN_KEY);
  storage?.removeItem(REFRESH_TOKEN_KEY);
  storage?.removeItem(EXPIRES_AT_KEY);
  clearCsrfToken();
}

function subscribeTokenRefresh(callback) {
  refreshSubscribers.push(callback);
}

function notifySubscribers(error, tokens) {
  refreshSubscribers.splice(0).forEach((callback) => callback(error, tokens));
}

async function requestRefreshToken() {
  const refreshToken = storage?.getItem(REFRESH_TOKEN_KEY);
  if (!refreshToken) {
    throw new Error('缺少刷新令牌');
  }

  try {
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/auth/refresh`,
      { refresh_token: refreshToken },
      {
        timeout: 8000,
        headers: { 'Content-Type': 'application/json' }
      }
    );
    const body = response.data || {};
    const inner = body.data !== undefined ? body.data : body;
    const token = inner.access_token || inner.accessToken;
    const newRefreshToken =
      inner.refresh_token || inner.refreshToken || refreshToken;
    const expiresIn = inner.expires_in || inner.expiresIn;
    const expiresAt = expiresIn
      ? Date.now() + Number(expiresIn) * 1000
      : Date.now() + 3600 * 1000;
    const tokens = {
      token,
      refreshToken: newRefreshToken,
      expiresAt
    };
    writeTokens(tokens);
    if (inner.csrfToken || inner.csrf_token) {
      setCsrfToken(inner.csrfToken || inner.csrf_token);
    }
    emitTokenEvent(tokens);
    return tokens;
  } catch (refreshError) {
    clearTokens();
    emitTokenEvent(null, 'auth:token-expired');
    throw normalizeHttpError(
      refreshError,
      'refresh_token无效或已过期，请重新登录'
    );
  }
}

http.interceptors.request.use(
  (config) => {
    activeRequests += 1;
    emitLoadingEvent();

    // 修复：尝试多种方式获取 token
    let token = storage?.getItem(TOKEN_KEY);

    // 如果直接获取失败，尝试从 auth 模块的存储格式获取
    if (!token) {
      try {
        const authState = storage?.getItem('vuex');
        if (authState) {
          const parsed = JSON.parse(authState);
          token = parsed?.auth?.token;
        }
      } catch (e) {
        console.warn('[HTTP] 无法从 Vuex 状态获取 token');
      }
    }

    if (token && !config.headers?.Authorization) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
      console.log('[HTTP] 添加 Authorization Header:', token.substring(0, 20) + '...');
    } else if (!token) {
      console.warn('[HTTP] 未找到 Token，请求将不带认证信息');
    }

    const csrfToken = getCsrfToken();
    if (csrfToken && !config.headers?.[CSRF_HEADER]) {
      config.headers = config.headers || {};
      config.headers[CSRF_HEADER] = csrfToken;
    }

    return config;
  },
  (error) => {
    decrementRequest();
    return Promise.reject(normalizeHttpError(error));
  }
);

http.interceptors.response.use(
  (response) => {
    decrementRequest();
    const csrfFromHeader =
      response.headers?.[CSRF_HEADER.toLowerCase()] ||
      response.headers?.[CSRF_HEADER];
    if (csrfFromHeader) {
      setCsrfToken(csrfFromHeader);
    }

    // 修复：保留完整的响应对象，而不是只返回 response.data
    // 这样 authAPI 可以正确处理嵌套的数据结构
    return response;
  },
  async (error) => {
    decrementRequest();

    const status = error?.response?.status;
    const config = error?.config || {};

    const reqUrl = String(config.url || '');
    const isRefreshCall = reqUrl.includes('/api/v1/auth/refresh');

    // 详细错误日志
    console.error('[HTTP Response Error]', {
      status,
      url: config.url,
      method: config.method,
      responseData: error?.response?.data
    });

    if (
      status === 401 &&
      !config.__isRetryRequest &&
      !config.skipAuthRefresh &&
      !isRefreshCall
    ) {
      if (!isRefreshing) {
        isRefreshing = true;
        refreshPromise = requestRefreshToken()
          .then((tokens) => {
            notifySubscribers(null, tokens);
            return tokens;
          })
          .catch((refreshError) => {
            notifySubscribers(refreshError);
            throw refreshError;
          })
          .finally(() => {
            isRefreshing = false;
            refreshPromise = null;
          });
      }

      return new Promise((resolve, reject) => {
        subscribeTokenRefresh((refreshError, tokens) => {
          if (refreshError || !tokens?.token) {
            reject(refreshError || new Error('刷新令牌失败'));
            return;
          }

          config.__isRetryRequest = true;
          config.headers = config.headers || {};
          config.headers.Authorization = `Bearer ${tokens.token}`;
          resolve(http(config));
        });
      });
    }

    if (status === 401) {
      console.warn('[HTTP] Token 已过期，清除认证信息');
      clearTokens();
      emitTokenEvent(null, 'auth:token-expired');
    }

    return Promise.reject(normalizeHttpError(error));
  }
);

export { API_BASE_URL, normalizeHttpError };
export default http;

