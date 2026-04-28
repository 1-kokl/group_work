import orderAPI from '../../services/api/order';

const state = () => ({
  orders: [],
  currentOrder: null,
  pagination: {
    page: 1,
    per_page: 10,
    total: 0,
    total_pages: 0
  },
  statusFilter: '',
  loading: false,
  error: null
});

const getters = {
  allOrders: (state) => state.orders,
  currentOrder: (state) => state.currentOrder,
  orderPagination: (state) => state.pagination,
  statusFilter: (state) => state.statusFilter,
  isLoading: (state) => state.loading,
  orderError: (state) => state.error,
  pendingOrders: (state) => state.orders.filter(o => o.status === 'pending'),
  paidOrders: (state) => state.orders.filter(o => o.status === 'paid'),
  shippedOrders: (state) => state.orders.filter(o => o.status === 'shipped'),
  completedOrders: (state) => state.orders.filter(o => o.status === 'completed'),
  cancelledOrders: (state) => state.orders.filter(o => o.status === 'cancelled')
};

const mutations = {
  SET_ORDERS(state, orders) {
    state.orders = orders;
  },
  SET_CURRENT_ORDER(state, order) {
    state.currentOrder = order;
  },
  UPDATE_ORDER(state, updatedOrder) {
    const index = state.orders.findIndex(o => o.id === updatedOrder.id);
    if (index !== -1) {
      state.orders[index] = { ...state.orders[index], ...updatedOrder };
    }
    if (state.currentOrder && state.currentOrder.id === updatedOrder.id) {
      state.currentOrder = { ...state.currentOrder, ...updatedOrder };
    }
  },
  SET_PAGINATION(state, pagination) {
    state.pagination = { ...state.pagination, ...pagination };
  },
  SET_STATUS_FILTER(state, status) {
    state.statusFilter = status;
  },
  ADD_ORDER(state, order) {
    state.orders.unshift(order);
  },
  SET_LOADING(state, loading) {
    state.loading = loading;
  },
  SET_ERROR(state, error) {
    state.error = error;
  },
  CLEAR_CURRENT_ORDER(state) {
    state.currentOrder = null;
  }
};

const actions = {
  async fetchOrders({ commit, state }) {
    commit('SET_LOADING', true);
    commit('SET_ERROR', null);

    try {
      const params = {
        page: state.pagination.page,
        per_page: state.pagination.per_page,
        status: state.statusFilter
      };

      const response = await orderAPI.getOrders(params);
      const data = response.data || response;

      commit('SET_ORDERS', data.items || []);
      commit('SET_PAGINATION', {
        page: data.page,
        per_page: data.per_page,
        total: data.total,
        total_pages: data.total_pages
      });

      return data;
    } catch (error) {
      commit('SET_ERROR', error.message || '获取订单列表失败');
      throw error;
    } finally {
      commit('SET_LOADING', false);
    }
  },

  async fetchOrderDetail({ commit }, id) {
    commit('SET_LOADING', true);
    commit('SET_ERROR', null);
    commit('CLEAR_CURRENT_ORDER');

    try {
      const response = await orderAPI.getOrderDetail(id);
      const data = response.data || response;

      commit('SET_CURRENT_ORDER', data);
      return data;
    } catch (error) {
      commit('SET_ERROR', error.message || '获取订单详情失败');
      throw error;
    } finally {
      commit('SET_LOADING', false);
    }
  },

  /* eslint-disable camelcase */
  async createOrder({ commit, dispatch }, { cartItemIds, shipping_address, contact_phone, remark }) {
    commit('SET_LOADING', true);
    commit('SET_ERROR', null);

    try {
      const response = await orderAPI.createOrder({
        cart_item_ids: cartItemIds,
        shipping_address,
        contact_phone,
        remark
      });
      const data = response.data || response;

      commit('ADD_ORDER', data);
      await dispatch('cart/clearCart', null, { root: true });

      return data;
    } catch (error) {
      commit('SET_ERROR', error.message || '创建订单失败');
      throw error;
    } finally {
      commit('SET_LOADING', false);
    }
  },

  async cancelOrder({ commit }, id) {
    commit('SET_LOADING', true);
    commit('SET_ERROR', null);

    try {
      const response = await orderAPI.cancelOrder(id);
      const data = response.data || response;

      commit('UPDATE_ORDER', data);
      return data;
    } catch (error) {
      commit('SET_ERROR', error.message || '取消订单失败');
      throw error;
    } finally {
      commit('SET_LOADING', false);
    }
  },

  async payOrder({ commit }, { id, paymentMethod }) {
    commit('SET_LOADING', true);
    commit('SET_ERROR', null);

    try {
      const response = await orderAPI.payOrder(id, paymentMethod);
      const data = response.data || response;

      commit('UPDATE_ORDER', data);
      return data;
    } catch (error) {
      commit('SET_ERROR', error.message || '支付失败');
      throw error;
    } finally {
      commit('SET_LOADING', false);
    }
  },

  async confirmReceipt({ commit }, id) {
    commit('SET_LOADING', true);
    commit('SET_ERROR', null);

    try {
      const response = await orderAPI.confirmReceipt(id);
      const data = response.data || response;

      commit('UPDATE_ORDER', data);
      return data;
    } catch (error) {
      commit('SET_ERROR', error.message || '确认收货失败');
      throw error;
    } finally {
      commit('SET_LOADING', false);
    }
  },

  setStatusFilter({ commit, dispatch }, status) {
    commit('SET_STATUS_FILTER', status);
    commit('SET_PAGINATION', { page: 1 });
    return dispatch('fetchOrders');
  },

  setPage({ commit, dispatch }, page) {
    commit('SET_PAGINATION', { page });
    return dispatch('fetchOrders');
  },

  clearFilter({ commit, dispatch }) {
    commit('SET_STATUS_FILTER', '');
    commit('SET_PAGINATION', { page: 1 });
    return dispatch('fetchOrders');
  }
};

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
};
