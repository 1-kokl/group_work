import http, { normalizeHttpError } from '../http';
import { getCache, setCache, clearCache } from '../../utils/cache';

const PROFILE_PATH = '/api/v1/users/me';
const PROFILE_CACHE_KEY = 'user:profile';
const DEVICE_CACHE_KEY = 'user:devices';

function unwrap(data) {
  if (data && typeof data === 'object' && data.data !== undefined) {
    return data.data;
  }
  return data;
}

function mapMePayload(raw) {
  if (!raw || typeof raw !== 'object') {
    return {};
  }
  return {
    username: raw.username,
    role: raw.role,
    phone: raw.phone_encrypted || raw.phone || '',
    email: raw.email || null,
    phoneMasked: raw.phone_encrypted
      ? String(raw.phone_encrypted).slice(0, 12) + '…'
      : ''
  };
}

export async function getProfile(options = {}) {
  const { force = false, cacheTtl = 5 * 60 * 1000 } = options || {};
  if (!force) {
    const cachedProfile = getCache(PROFILE_CACHE_KEY);
    if (cachedProfile) {
      return cachedProfile;
    }
  }

  try {
    const response = await http.get(PROFILE_PATH);
    const profile = mapMePayload(unwrap(response));
    setCache(PROFILE_CACHE_KEY, profile, cacheTtl);
    return profile;
  } catch (error) {
    throw normalizeHttpError(error, '获取用户信息失败，请稍后重试。');
  }
}

export async function updateProfile(payload = {}) {
  try {
    const { phone, ...rest } = payload;
    let result = null;

    if (Object.keys(rest).length) {
      console.warn(
        '[userAPI] 后端暂未提供 PATCH /users/me，已忽略字段:',
        Object.keys(rest)
      );
    }

    if (phone !== undefined) {
      result = await http.patch(`${PROFILE_PATH}/phone`, { phone });
    }

    clearCache(PROFILE_CACHE_KEY);
    return result;
  } catch (error) {
    throw normalizeHttpError(error, '更新个人信息失败，请稍后再试。');
  }
}

export async function changePassword() {
  const err = new Error('后端暂未提供修改密码接口。');
  err.status = 501;
  throw err;
}

export async function getDevices() {
  return [];
}

export function invalidateUserCaches() {
  clearCache(PROFILE_CACHE_KEY);
  clearCache(DEVICE_CACHE_KEY);
}

export default {
  getProfile,
  updateProfile,
  changePassword,
  getDevices,
  invalidateUserCaches
};
