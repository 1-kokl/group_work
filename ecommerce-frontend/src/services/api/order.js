/* eslint-disable camelcase */
import http from '../http';

const API_PREFIX = '/api/ecommerce';

/**
 * 获取订单列表
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.per_page - 每页数量
 * @param {string} params.status - 订单状态 (pending, paid, shipped, completed, cancelled)
 */
export async function getOrders(params = {}) {
  return http.get(`${API_PREFIX}/orders`, {
    params: {
      page: params.page || 1,
      per_page: params.per_page || 10,
      status: params.status || ''
    }
  });
}

/**
 * 获取订单详情
 * @param {number|string} id - 订单ID
 */
export async function getOrderDetail(id) {
  return http.get(`${API_PREFIX}/orders/${id}`);
}

/**
 * 创建订单（从购物车结算）
 * @param {Object} data - { cart_item_ids: [], address_id }
 */
export async function createOrder(data) {
  return http.post(`${API_PREFIX}/orders`, data);
}

/**
 * 取消订单
 * @param {number|string} id - 订单ID
 */
export async function cancelOrder(id) {
  return http.put(`${API_PREFIX}/orders/${id}/cancel`);
}

/**
 * 支付订单
 * @param {number|string} id - 订单ID
 * @param {string} payment_method - 支付方式
 */
export async function payOrder(id, payment_method = 'alipay') {
  return http.post(`${API_PREFIX}/orders/${id}/pay`, { payment_method });
}

/**
 * 确认收货
 * @param {number|string} id - 订单ID
 */
export async function confirmReceipt(id) {
  return http.post(`${API_PREFIX}/orders/${id}/confirm`);
}

export default {
  getOrders,
  getOrderDetail,
  createOrder,
  cancelOrder,
  payOrder,
  confirmReceipt
};
