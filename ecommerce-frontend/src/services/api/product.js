import http from '../http';

const API_PREFIX = '/api/ecommerce';

/**
 * 获取商品列表
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.per_page - 每页数量
 * @param {string} params.keyword - 搜索关键词
 * @param {string} params.category - 商品分类
 * @param {string} params.sort - 排序方式 (price_asc, price_desc, created_desc)
 */
export async function getProducts(params = {}) {
  return http.get(`${API_PREFIX}/products`, {
    params: {
      page: params.page || 1,
      per_page: params.per_page || 10,
      keyword: params.keyword || '',
      category: params.category || '',
      sort: params.sort || 'created_desc'
    }
  });
}

/**
 * 获取商品详情
 * @param {number|string} id - 商品ID
 */
export async function getProductDetail(id) {
  return http.get(`${API_PREFIX}/products/${id}`);
}

/**
 * 创建商品
 * @param {Object} data - 商品数据
 */
export async function createProduct(data) {
  return http.post(`${API_PREFIX}/products`, data);
}

/**
 * 更新商品
 * @param {number|string} id - 商品ID
 * @param {Object} data - 商品数据
 */
export async function updateProduct(id, data) {
  return http.put(`${API_PREFIX}/products/${id}`, data);
}

/**
 * 删除商品
 * @param {number|string} id - 商品ID
 */
export async function deleteProduct(id) {
  return http.delete(`${API_PREFIX}/products/${id}`);
}

/**
 * 获取商品分类列表
 */
export async function getCategories() {
  return http.get(`${API_PREFIX}/categories`);
}

export default {
  getProducts,
  getProductDetail,
  createProduct,
  updateProduct,
  deleteProduct,
  getCategories
};
