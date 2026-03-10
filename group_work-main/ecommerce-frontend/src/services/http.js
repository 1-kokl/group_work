import axios from 'axios';

const API_BASE_URL =
  process.env.VUE_APP_API_BASE_URL ||
  process.env.API_BASE_URL ||
  'http://localhost:5000';

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
  let message =
    error?.response?.data?.message ||
    ERROR_CODE_MESSAGES[code] ||
    (status === 0
      ? '网络连接异常，请检查网络后重试。'
      : fallbackMessage);
  const details = error?.response?.data?.errors || null;

  if (
    status === 401 &&
    typeof error?.config?.url === 'string' &&
    error.config.url.includes('/api/v1/user/login')
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
      `${API_BASE_URL}/api/v1/user/token/refresh`,
      { refreshToken },
      {
        timeout: 8000,
        headers: { 'Content-Type': 'application/json' }
      }
    );
    const {
      token,
      refreshToken: newRefreshToken,
      expiresIn,
      csrfToken: responseCsrfToken
    } = response.data;
    const expiresAt = Date.now() + Number(expiresIn || 0) * 1000;
    const tokens = { token, refreshToken: newRefreshToken, expiresAt };
    writeTokens(tokens);
    if (responseCsrfToken) {
      setCsrfToken(responseCsrfToken);
    }
    emitTokenEvent(tokens);
    return tokens;
  } catch (refreshError) {
    clearTokens();
    emitTokenEvent(null, 'auth:token-expired');
    throw normalizeHttpError(refreshError, '刷新登录状态失败，请重新登录。');
  }
}

http.interceptors.request.use(
  (config) => {
    activeRequests += 1;
    emitLoadingEvent();

    const token = storage?.getItem(TOKEN_KEY);
    if (token && !config.headers?.Authorization) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
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
    return response.data;
  },
  async (error) => {
    decrementRequest();

    const status = error?.response?.status;
    const config = error?.config || {};

    if (
      status === 401 &&
      !config.__isRetryRequest &&
      !config.skipAuthRefresh
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
      clearTokens();
      emitTokenEvent(null, 'auth:token-expired');
    }

    return Promise.reject(normalizeHttpError(error));
  }
);

export { API_BASE_URL, normalizeHttpError };
export default http;

