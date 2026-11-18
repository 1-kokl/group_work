const STORAGE_PREFIX = 'cache:';

/**
 * 将数据存入本地缓存
 * @param {string} key 缓存键
 * @param {any} value 缓存值
 * @param {number} ttl 过期时间（毫秒）
 */
export function setCache(key, value, ttl = 300000) {
  try {
    const payload = {
      value,
      expiredAt: ttl ? Date.now() + Number(ttl) : null
    };
    localStorage.setItem(`${STORAGE_PREFIX}${key}`, JSON.stringify(payload));
  } catch (error) {
    console.warn('[cache] 设置缓存失败:', error);
  }
}

/**
 * 读取本地缓存
 * @param {string} key 缓存键
 * @returns {any|null}
 */
export function getCache(key) {
  try {
    const raw = localStorage.getItem(`${STORAGE_PREFIX}${key}`);
    if (!raw) return null;
    const payload = JSON.parse(raw);
    if (payload.expiredAt && Date.now() > payload.expiredAt) {
      localStorage.removeItem(`${STORAGE_PREFIX}${key}`);
      return null;
    }
    return payload.value;
  } catch (error) {
    console.warn('[cache] 读取缓存失败:', error);
    localStorage.removeItem(`${STORAGE_PREFIX}${key}`);
    return null;
  }
}

/**
 * 清除指定缓存
 * @param {string} key 缓存键
 */
export function clearCache(key) {
  try {
    localStorage.removeItem(`${STORAGE_PREFIX}${key}`);
  } catch (error) {
    console.warn('[cache] 清理缓存失败:', error);
  }
}

/**
 * 清空所有缓存
 */
export function clearAllCache() {
  try {
    Object.keys(localStorage)
      .filter((key) => key.startsWith(STORAGE_PREFIX))
      .forEach((key) => localStorage.removeItem(key));
  } catch (error) {
    console.warn('[cache] 清空缓存失败:', error);
  }
}

