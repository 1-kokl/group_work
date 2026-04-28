import productAPI from '../../services/api/product';

const state = () => ({
  products: [],
  currentProduct: null,
  categories: [],
  pagination: {
    page: 1,
    per_page: 10,
    total: 0,
    total_pages: 0
  },
  filters: {
    keyword: '',
    category: '',
    sort: 'created_desc'
  },
  loading: false,
  error: null
});

const getters = {
  allProducts: (state) => state.products,
  currentProduct: (state) => state.currentProduct,
  allCategories: (state) => state.categories,
  productPagination: (state) => state.pagination,
  productFilters: (state) => state.filters,
  isLoading: (state) => state.loading,
  productError: (state) => state.error
};

const mutations = {
  SET_PRODUCTS(state, products) {
    state.products = products;
  },
  SET_CURRENT_PRODUCT(state, product) {
    state.currentProduct = product;
  },
  SET_CATEGORIES(state, categories) {
    state.categories = categories;
  },
  SET_PAGINATION(state, pagination) {
    state.pagination = { ...state.pagination, ...pagination };
  },
  SET_FILTERS(state, filters) {
    state.filters = { ...state.filters, ...filters };
  },
  SET_LOADING(state, loading) {
    state.loading = loading;
  },
  SET_ERROR(state, error) {
    state.error = error;
  },
  CLEAR_CURRENT_PRODUCT(state) {
    state.currentProduct = null;
  }
};

const actions = {
  async fetchProducts({ commit, state }) {
    commit('SET_LOADING', true);
    commit('SET_ERROR', null);

    try {
      const params = {
        page: state.pagination.page,
        per_page: state.pagination.per_page,
        keyword: state.filters.keyword,
        category: state.filters.category,
        sort: state.filters.sort
      };

      const response = await productAPI.getProducts(params);
      const data = response.data || response;

      commit('SET_PRODUCTS', data.items || []);
      commit('SET_PAGINATION', {
        page: data.page,
        per_page: data.per_page,
        total: data.total,
        total_pages: data.total_pages
      });

      return data;
    } catch (error) {
      commit('SET_ERROR', error.message || '获取商品列表失败');
      throw error;
    } finally {
      commit('SET_LOADING', false);
    }
  },

  async fetchProductDetail({ commit }, id) {
    commit('SET_LOADING', true);
    commit('SET_ERROR', null);
    commit('CLEAR_CURRENT_PRODUCT');

    try {
      const response = await productAPI.getProductDetail(id);
      const data = response.data || response;

      commit('SET_CURRENT_PRODUCT', data);
      return data;
    } catch (error) {
      commit('SET_ERROR', error.message || '获取商品详情失败');
      throw error;
    } finally {
      commit('SET_LOADING', false);
    }
  },

  async fetchCategories({ commit }) {
    try {
      const response = await productAPI.getCategories();
      const data = response.data || response;

      commit('SET_CATEGORIES', data);
      return data;
    } catch (error) {
      commit('SET_ERROR', error.message || '获取分类失败');
      throw error;
    }
  },

  async createProduct({ commit }, productData) {
    commit('SET_LOADING', true);
    commit('SET_ERROR', null);

    try {
      const response = await productAPI.createProduct(productData);
      const data = response.data || response;

      commit('SET_LOADING', false);
      return data;
    } catch (error) {
      commit('SET_ERROR', error.message || '创建商品失败');
      throw error;
    }
  },

  async updateProduct({ commit }, { id, data }) {
    commit('SET_LOADING', true);
    commit('SET_ERROR', null);

    try {
      const response = await productAPI.updateProduct(id, data);
      const result = response.data || response;

      commit('SET_CURRENT_PRODUCT', result);
      commit('SET_LOADING', false);
      return result;
    } catch (error) {
      commit('SET_ERROR', error.message || '更新商品失败');
      throw error;
    }
  },

  async deleteProduct({ commit }, id) {
    commit('SET_LOADING', true);
    commit('SET_ERROR', null);

    try {
      await productAPI.deleteProduct(id);

      commit('SET_LOADING', false);
      return true;
    } catch (error) {
      commit('SET_ERROR', error.message || '删除商品失败');
      throw error;
    }
  },

  setFilters({ commit, dispatch }, filters) {
    commit('SET_FILTERS', filters);
    commit('SET_PAGINATION', { page: 1 });
    return dispatch('fetchProducts');
  },

  setPage({ commit, dispatch }, page) {
    commit('SET_PAGINATION', { page });
    return dispatch('fetchProducts');
  },

  clearFilters({ commit, dispatch }) {
    commit('SET_FILTERS', {
      keyword: '',
      category: '',
      sort: 'created_desc'
    });
    commit('SET_PAGINATION', { page: 1 });
    return dispatch('fetchProducts');
  }
};

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
};
