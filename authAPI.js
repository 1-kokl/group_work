/* 与 Nzs/group_work-main/ecommerce-frontend/src/services/api/authAPI.js 保持同步 */
import axios from 'axios';
import http, { API_BASE_URL, normalizeHttpError } from '../http';

const AUTH_PREFIX = '/api/v1/auth';
const REGISTER_PATH = '/api/v1/users';
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
      role: data?.data?.role ?? null
    });
  } catch (error) {
    const normalized = normalizeAuthError(error);
    throw normalized;
  }
}

export async function register(payload) {
  try {
    const data = await http.post(
      REGISTER_PATH,
      {
        username: payload.username,
        password: payload.password,
        phone: payload.phone
      },
      { skipAuthRefresh: true }
    );
    const inner = unwrapPayload(data);
    return {
      username: inner?.username ?? payload.username,
      raw: data
    };
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
  try {
    sessionStorage.removeItem(CSRF_STORAGE_KEY);
  } catch (e) {
    /* ignore */
  }
}

export async function refreshToken(refreshTokenValue) {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/auth/refresh`,
      { refresh_token: refreshTokenValue },
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 8000
      }
    );
    return normalizeAuthResponse(response.data, {
      existingRefresh: refreshTokenValue
    });
  } catch (error) {
    throw normalizeHttpError(
      error,
      'refresh_token无效或已过期，请重新登录'
    );
  }
}

function unwrapPayload(data) {
  if (data && typeof data === 'object' && data.data !== undefined) {
    return data.data;
  }
  return data;
}

function normalizeAuthResponse(data = {}, meta = {}) {
  const payload = unwrapPayload(data);
  const p = payload && typeof payload === 'object' ? payload : {};

  const token =
    p.token ||
    p.accessToken ||
    p.access_token ||
    data.token ||
    null;
  const refreshToken =
    p.refreshToken ||
    p.refresh_token ||
    data.refreshToken ||
    meta.existingRefresh ||
    null;
  const expiresIn =
    p.expiresIn || p.expires_in || data.expiresIn || null;
  const csrfToken =
    p.csrfToken || p.csrf_token || data.csrfToken || null;
  const inferredUser =
    p.user ||
    data.user ||
    meta.user ||
    (meta.username ||
    p.username ||
    data.username ||
    meta.email ||
    p.email ||
    data.email
      ? {
          username:
            meta.username || p.username || data.username || null,
          role: meta.role || p.role || data.role || 'user',
          roles:
            meta.roles ||
            p.roles ||
            [meta.role || p.role || data.role || 'user'].filter(Boolean),
          phone: meta.phone || p.phone || data.phone || null,
          email: meta.email || p.email || data.email || null
        }
      : null);

  let expiresAt = p.expiresAt
    ? Number(p.expiresAt)
    : expiresIn
      ? Date.now() + Number(expiresIn) * 1000
      : null;
  if (token && !expiresAt) {
    expiresAt = Date.now() + 3600 * 1000;
  }

  if (csrfToken) {
    try {
      sessionStorage.setItem(CSRF_STORAGE_KEY, csrfToken);
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
