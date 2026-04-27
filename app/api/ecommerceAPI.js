import request from '@/services/http';

// ==================== 商品 API ====================

/**
 * 获取商品列表
 * @param {Object} params - 查询参数 {page, per_page, category, status, keyword}
 */
export const getProductList = (params) => {
  return request({
    url: '/api/ecommerce/products',
    method: 'GET',
    params
  });
};

/**
 * 获取商品详情
 * @param {string} productId - 商品ID
 */
export const getProductDetail = (productId) => {
  return request({
    url: `/api/ecommerce/products/${productId}`,
    method: 'GET'
  });
};

/**
 * 创建商品（需要管理员权限）
 * @param {Object} data - 商品信息
 */
export const createProduct = (data) => {
  return request({
    url: '/api/ecommerce/products',
    method: 'POST',
    data
  });
};

/**
 * 更新商品
 * @param {string} productId - 商品ID
 * @param {Object} data - 更新数据
 */
export const updateProduct = (productId, data) => {
  return request({
    url: `/api/ecommerce/products/${productId}`,
    method: 'PUT',
    data
  });
};

/**
 * 删除商品（软删除）
 * @param {string} productId - 商品ID
 */
export const deleteProduct = (productId) => {
  return request({
    url: `/api/ecommerce/products/${productId}`,
    method: 'DELETE'
  });
};

// ==================== 购物车 API ====================

/**
 * 添加商品到购物车
 * @param {Object} data - {product_id, quantity}
 */
export const addToCart = (data) => {
  return request({
    url: '/api/ecommerce/cart',
    method: 'POST',
    data
  });
};

/**
 * 获取购物车列表
 */
export const getCartList = () => {
  return request({
    url: '/api/ecommerce/cart',
    method: 'GET'
  });
};

/**
 * 更新购物车项
 * @param {string} cartId - 购物车项ID
 * @param {Object} data - {quantity, selected}
 */
export const updateCartItem = (cartId, data) => {
  return request({
    url: `/api/ecommerce/cart/${cartId}`,
    method: 'PUT',
    data
  });
};

/**
 * 从购物车移除
 * @param {string} cartId - 购物车项ID
 */
export const removeFromCart = (cartId) => {
  return request({
    url: `/api/ecommerce/cart/${cartId}`,
    method: 'DELETE'
  });
};

/**
 * 清空购物车
 */
export const clearCart = () => {
  return request({
    url: '/api/ecommerce/cart/clear',
    method: 'DELETE'
  });
};

// ==================== 订单 API ====================

/**
 * 创建订单
 * @param {Object} data - {shipping_address, contact_phone, remark, cart_item_ids}
 */
export const createOrder = (data) => {
  return request({
    url: '/api/ecommerce/orders',
    method: 'POST',
    data
  });
};

/**
 * 获取订单详情
 * @param {string} orderId - 订单ID
 */
export const getOrderDetail = (orderId) => {
  return request({
    url: `/api/ecommerce/orders/${orderId}`,
    method: 'GET'
  });
};

/**
 * 获取订单列表
 * @param {Object} params - {page, per_page, status}
 */
export const getOrderList = (params) => {
  return request({
    url: '/api/ecommerce/orders',
    method: 'GET',
    params
  });
};

/**
 * 取消订单
 * @param {string} orderId - 订单ID
 */
export const cancelOrder = (orderId) => {
  return request({
    url: `/api/ecommerce/orders/${orderId}/cancel`,
    method: 'POST'
  });
};

/**
 * 支付订单
 * @param {string} orderId - 订单ID
 */
export const payOrder = (orderId) => {
  return request({
    url: `/api/ecommerce/orders/${orderId}/pay`,
    method: 'POST'
  });
};
