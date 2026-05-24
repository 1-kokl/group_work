import http from '../http';

/**
 * 获取用户订单列表
 */
export function getUserOrders(params = {}) {
  return http.get('/api/ecommerce/orders', { params });
}

/**
 * 获取订单详情
 */
export function getOrderDetail(orderId) {
  return http.get(`/api/ecommerce/orders/${orderId}`);
}

/**
 * 取消订单
 */
export function cancelOrder(orderId) {
  return http.post(`/api/ecommerce/orders/${orderId}/cancel`);
}

/**
 * 创建支付请求
 */
export function createPayment(orderId) {
  return http.post(`/api/pay/create/${orderId}`);
}

export default {
  getUserOrders,
  getOrderDetail,
  cancelOrder,
  createPayment
};
