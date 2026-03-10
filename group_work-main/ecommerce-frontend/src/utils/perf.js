/**
 * 创建一个异步防抖函数
 * @param {Function} fn 原始异步函数
 * @param {number} delay 防抖延迟（毫秒）
 * @returns {Function} 防抖后的异步函数
 */
export function debounceAsync(fn, delay = 300) {
  let timer = null;
  let pendingReject = null;

  return (...args) =>
    new Promise((resolve, reject) => {
      if (timer) {
        clearTimeout(timer);
        if (pendingReject) pendingReject(new Error('REQUEST_DEBOUNCED'));
      }

      pendingReject = reject;
      timer = setTimeout(async () => {
        timer = null;
        pendingReject = null;
        try {
          const result = await fn(...args);
          resolve(result);
        } catch (error) {
          reject(error);
        }
      }, delay);
    });
}

/**
 * 简易的节流函数
 * @param {Function} fn 原始函数
 * @param {number} interval 节流间隔（毫秒）
 * @returns {Function}
 */
export function throttle(fn, interval = 300) {
  let lastTime = 0;
  return (...args) => {
    const now = Date.now();
    if (now - lastTime >= interval) {
      lastTime = now;
      fn(...args);
    }
  };
}

