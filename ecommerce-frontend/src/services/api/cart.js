import http from '../http';

const API_PREFIX = '/api/ecommerce';

/**
 * 获取购物车列表
 */
export async function getCart() {
  return http.get(`${API_PREFIX}/cart`);
}

/**
 * 添加商品到购物车
 * @param {Object} data - { product_id, quantity }
 */
export async function addToCart(data) {
  return http.post(`${API_PREFIX}/cart/add`, data);
}

/**
 * 更新购物车商品数量
 * @param {number|string} cartId - 购物车项ID
 * @param {number} quantity - 数量
 */
export async function updateCartQuantity(cartId, quantity) {
  return http.put(`${API_PREFIX}/cart/${cartId}`, { quantity });
}

/**
 * 从购物车移除商品
 * @param {number|string} cartId - 购物车项ID
 */
export async function removeFromCart(cartId) {
  return http.delete(`${API_PREFIX}/cart/${cartId}`);
}

/**
 * 清空购物车
 */
export async function clearCart() {
  return http.delete(`${API_PREFIX}/cart`);
}

/**
 * 批量删除购物车商品
 * @param {Array} ids - 购物车项ID数组
 */
export async function batchRemoveFromCart(ids) {
  return http.post(`${API_PREFIX}/cart/batch-delete`, { ids });
}

export default {
  getCart,
  addToCart,
  updateCartQuantity,
  removeFromCart,
  clearCart,
  batchRemoveFromCart
};
