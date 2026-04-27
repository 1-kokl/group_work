import cartAPI from '../../services/api/cart';

const CART_STORAGE_KEY = 'ecommerce.cart';

function loadCartFromStorage() {
  try {
    const stored = localStorage.getItem(CART_STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

function saveCartToStorage(items) {
  try {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items));
  } catch (error) {
    console.warn('[cart] 保存购物车到本地存储失败:', error);
  }
}

const state = () => ({
  items: loadCartFromStorage(),
  loading: false,
  error: null
});

const getters = {
  cartItems: (state) => state.items,
  cartItemCount: (state) => state.items.reduce((sum, item) => sum + item.quantity, 0),
  selectedItems: (state) => state.items.filter(item => item.selected),
  selectedCount: (state) => state.items.filter(item => item.selected).length,
  totalAmount: (state) => {
    return state.items
      .filter(item => item.selected)
      .reduce((sum, item) => sum + (item.product?.price || 0) * item.quantity, 0);
  },
  isLoading: (state) => state.loading,
  cartError: (state) => state.error,
  isAllSelected: (state) => {
    if (state.items.length === 0) return false;
    return state.items.every(item => item.selected);
  }
};

const mutations = {
  SET_ITEMS(state, items) {
    state.items = items;
    saveCartToStorage(items);
  },
  ADD_ITEM(state, item) {
    const existingIndex = state.items.findIndex(i => i.product_id === item.product_id);
    if (existingIndex !== -1) {
      state.items[existingIndex].quantity += item.quantity;
      state.items[existingIndex].updated_at = new Date().toISOString();
    } else {
      state.items.push({
        ...item,
        selected: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      });
    }
    saveCartToStorage(state.items);
  },
  UPDATE_QUANTITY(state, { cartId, quantity }) {
    const item = state.items.find(i => i.id === cartId);
    if (item) {
      item.quantity = quantity;
      item.updated_at = new Date().toISOString();
      saveCartToStorage(state.items);
    }
  },
  REMOVE_ITEM(state, cartId) {
    state.items = state.items.filter(i => i.id !== cartId);
    saveCartToStorage(state.items);
  },
  TOGGLE_SELECT(state, { cartId, selected }) {
    const item = state.items.find(i => i.id === cartId);
    if (item) {
      item.selected = selected;
      saveCartToStorage(state.items);
    }
  },
  TOGGLE_ALL_SELECT(state, selected) {
    state.items.forEach(item => {
      item.selected = selected;
    });
    saveCartToStorage(state.items);
  },
  CLEAR_CART(state) {
    state.items = [];
    saveCartToStorage([]);
  },
  SYNC_FROM_SERVER(state, items) {
    const localItems = state.items;
    const mergedItems = items.map(serverItem => {
      const localItem = localItems.find(li => li.product_id === serverItem.product_id);
      return localItem ? { ...serverItem, selected: localItem.selected } : serverItem;
    });
    state.items = mergedItems;
    saveCartToStorage(mergedItems);
  },
  SET_LOADING(state, loading) {
    state.loading = loading;
  },
  SET_ERROR(state, error) {
    state.error = error;
  }
};

const actions = {
  async fetchCart({ commit }) {
    commit('SET_LOADING', true);
    commit('SET_ERROR', null);

    try {
      const response = await cartAPI.getCart();
      const data = response.data || response;
      const items = data.items || data.data?.items || [];

      commit('SET_ITEMS', items);
      return data;
    } catch (error) {
      commit('SET_ERROR', error.message || '获取购物车失败');
      throw error;
    } finally {
      commit('SET_LOADING', false);
    }
  },

  async addToCart({ commit, state }, { product, quantity = 1 }) {
    commit('SET_LOADING', true);
    commit('SET_ERROR', null);

    try {
      const existingItem = state.items.find(item => item.product_id === product.id);
      if (existingItem) {
        const newQuantity = existingItem.quantity + quantity;
        await cartAPI.updateCartQuantity(existingItem.id, newQuantity);
        commit('UPDATE_QUANTITY', { cartId: existingItem.id, quantity: newQuantity });
      } else {
        const response = await cartAPI.addToCart({
          product_id: product.id,
          quantity
        });
        const data = response.data || response;
        const newItem = {
          id: data.id || Date.now(),
          product_id: product.id,
          quantity,
          product
        };
        commit('ADD_ITEM', newItem);
      }

      return true;
    } catch (error) {
      commit('SET_ERROR', error.message || '加入购物车失败');
      throw error;
    } finally {
      commit('SET_LOADING', false);
    }
  },

  async updateQuantity({ commit }, { cartId, quantity }) {
    commit('SET_ERROR', null);

    try {
      if (quantity < 1) return;
      await cartAPI.updateCartQuantity(cartId, quantity);
      commit('UPDATE_QUANTITY', { cartId, quantity });
    } catch (error) {
      commit('SET_ERROR', error.message || '更新数量失败');
      throw error;
    }
  },

  async removeItem({ commit }, cartId) {
    commit('SET_ERROR', null);

    try {
      await cartAPI.removeFromCart(cartId);
      commit('REMOVE_ITEM', cartId);
    } catch (error) {
      commit('SET_ERROR', error.message || '移除商品失败');
      throw error;
    }
  },

  async batchRemove({ commit, state }, cartIds) {
    commit('SET_ERROR', null);

    try {
      await cartAPI.batchRemoveFromCart(cartIds);
      commit('SET_ITEMS', state.items.filter(item => !cartIds.includes(item.id)));
    } catch (error) {
      commit('SET_ERROR', error.message || '批量删除失败');
      throw error;
    }
  },

  async clearCart({ commit }) {
    commit('SET_ERROR', null);

    try {
      await cartAPI.clearCart();
      commit('CLEAR_CART');
    } catch (error) {
      commit('SET_ERROR', error.message || '清空购物车失败');
      throw error;
    }
  },

  toggleSelect({ commit }, { cartId, selected }) {
    commit('TOGGLE_SELECT', { cartId, selected });
  },

  toggleAllSelect({ commit, state }) {
    const isAllSelected = state.items.length > 0 && state.items.every(item => item.selected);
    commit('TOGGLE_ALL_SELECT', !isAllSelected);
  },

  getSelectedItems({ state, getters }) {
    return getters.selectedItems;
  }
};

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
};
