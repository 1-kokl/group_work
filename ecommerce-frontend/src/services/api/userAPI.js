import http, { normalizeHttpError } from '../http';
import { getCache, setCache, clearCache } from '../../utils/cache';

const USER_PREFIX = '/api/v1/user';
const PROFILE_PREFIX = '/api/v1/users/me';
const PROFILE_CACHE_KEY = 'user:profile';
const DEVICE_CACHE_KEY = 'user:devices';

export async function getProfile(options = {}) {
  const { force = false, cacheTtl = 5 * 60 * 1000 } = options || {};
  if (!force) {
    const cachedProfile = getCache(PROFILE_CACHE_KEY);
    if (cachedProfile) {
      return cachedProfile;
    }
  }

  try {
    const response = await http.get(`${USER_PREFIX}/info`);
    const profile = response?.data || response;
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
      result = await http.patch(`${PROFILE_PREFIX}`, rest);
    }

    if (phone !== undefined) {
      result = await http.patch(`${PROFILE_PREFIX}/phone`, { phone });
    }

    clearCache(PROFILE_CACHE_KEY);
    return result;
  } catch (error) {
    throw normalizeHttpError(error, '更新个人信息失败，请稍后再试。');
  }
}

export async function changePassword(payload) {
  try {
    return await http.post(`${USER_PREFIX}/change-password`, payload);
  } catch (error) {
    throw normalizeHttpError(error, '修改密码失败，请检查后再试。');
  }
}

export async function getDevices() {
  try {
    const cachedDevices = getCache(DEVICE_CACHE_KEY);
    if (cachedDevices) {
      return cachedDevices;
    }

    const result = await http.get(`${USER_PREFIX}/devices`);
    const devices = Array.isArray(result) ? result : [];
    setCache(DEVICE_CACHE_KEY, devices, 5 * 60 * 1000);
    return devices;
  } catch (error) {
    throw normalizeHttpError(error, '获取登录设备失败，请稍后再试。');
  }
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

