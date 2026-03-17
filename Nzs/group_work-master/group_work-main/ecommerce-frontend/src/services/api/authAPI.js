import axios from 'axios';
import http, { API_BASE_URL, normalizeHttpError } from '../http';

const AUTH_PREFIX = '/api/v1/user';
const CSRF_STORAGE_KEY = 'auth.csrfToken';

export async function login(credentials) {
  const payload = normalizeLoginPayload(credentials);
  try {
    const data = await http.post(`${AUTH_PREFIX}/login`, payload, {
      skipAuthRefresh: true,
      suppressErrorEvent: true
    });
    return normalizeAuthResponse(data, {
      username: payload.username,
      role:
        data?.data?.role ||
        data?.role ||
        null
    });
  } catch (error) {
    const normalized = normalizeAuthError(error);
    throw normalized;
  }
}

export async function register(payload) {
  try {
    const data = await http.post(`${AUTH_PREFIX}/register`, payload, {
      skipAuthRefresh: true
    });
    return normalizeAuthResponse(data, {
      username: payload.username,
      phone: payload.phone,
      email: payload.email
    });
  } catch (error) {
    throw normalizeHttpError(error, '注册失败，请稍后再试。');
  }
}

export async function logout() {
  try {
    await http.post(`${AUTH_PREFIX}/logout`);
  } catch (error) {
    throw normalizeHttpError(error, '退出登录失败，请稍后再试。');
  }
  localStorage.removeItem(CSRF_STORAGE_KEY);
}

export async function refreshToken(refreshToken) {
  try {
    const response = await axios.post(
      `${API_BASE_URL}${AUTH_PREFIX}/token/refresh`,
      { refreshToken },
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 8000
      }
    );
    return normalizeAuthResponse(response.data);
  } catch (error) {
    throw normalizeHttpError(error, '刷新登录状态失败，请重新登录。');
  }
}

function normalizeAuthResponse(data = {}, meta = {}) {
  const payload =
    data && typeof data === 'object' && typeof data.data === 'object'
      ? data.data
      : data;

  const token =
    payload.token ||
    payload.accessToken ||
    payload.access_token ||
    data.token ||
    null;
  const refreshToken =
    payload.refreshToken ||
    payload.refresh_token ||
    data.refreshToken ||
    null;
  const expiresIn =
    payload.expiresIn ||
    payload.expires_in ||
    data.expiresIn ||
    null;
  const csrfToken =
    payload.csrfToken || payload.csrf_token || data.csrfToken || null;
  const inferredUser =
    payload.user ||
    data.user ||
    meta.user ||
    (meta.username ||
    payload.username ||
    data.username ||
    meta.email ||
    payload.email
      ? {
          username:
            meta.username || payload.username || data.username || null,
          role: meta.role || payload.role || data.role || null,
          phone: meta.phone || payload.phone || data.phone || null,
          email: meta.email || payload.email || data.email || null
        }
      : null);

  const expiresAt = payload.expiresAt
    ? Number(payload.expiresAt)
    : expiresIn
      ? Date.now() + Number(expiresIn) * 1000
      : null;

  if (csrfToken) {
    try {
      localStorage.setItem(CSRF_STORAGE_KEY, csrfToken);
    } catch (error) {
      console.warn('[authAPI] 存储 CSRF 令牌失败:', error);
    }
  }
  return {
    token,
    refreshToken,
    expiresAt,
    user: inferredUser,
    raw: data
  };
}

function normalizeLoginPayload(credentials = {}) {
  const payload = { ...credentials };
  if (payload.identifier && !payload.username) {
    payload.username = payload.identifier;
  }
  delete payload.identifier;
  delete payload.remember;
  return payload;
}

function normalizeAuthError(error) {
  const normalized = normalizeHttpError(error, '登录失败，请检查账号信息。');
  if (normalized.status === 401) {
    normalized.message = '用户名或密码错误，请重试。';
  }
  return normalized;
}

export default {
  login,
  register,
  logout,
  refreshToken
};

