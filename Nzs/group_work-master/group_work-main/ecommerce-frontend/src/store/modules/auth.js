import authAPI from '../../services/api/authAPI';

const storage = typeof window !== 'undefined' ? window.sessionStorage : null;
const TOKEN_STORAGE_KEY = 'auth.token';
const REFRESH_STORAGE_KEY = 'auth.refreshToken';
const EXPIRES_STORAGE_KEY = 'auth.expiresAt';
const USER_STORAGE_KEY = 'auth.user';
const REMEMBER_STORAGE_KEY = 'auth.remember';

function readJson(key) {
  try {
    if (!storage) return null;
    const raw = storage.getItem(key);
    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    console.warn(`[auth] 读取 ${key} 失败:`, error);
    return null;
  }
}

function writeJson(key, value) {
  try {
    if (!storage) return;
    if (value === null || value === undefined) {
      storage.removeItem(key);
    } else {
      storage.setItem(key, JSON.stringify(value));
    }
  } catch (error) {
    console.warn(`[auth] 写入 ${key} 失败:`, error);
  }
}

function writeTokens(state) {
  try {
    if (!storage) return;
    if (state.token) {
      storage.setItem(TOKEN_STORAGE_KEY, state.token);
    } else {
      storage.removeItem(TOKEN_STORAGE_KEY);
    }

    if (state.refreshToken) {
      storage.setItem(REFRESH_STORAGE_KEY, state.refreshToken);
    } else {
      storage.removeItem(REFRESH_STORAGE_KEY);
    }

    if (state.expiresAt) {
      storage.setItem(EXPIRES_STORAGE_KEY, String(state.expiresAt));
    } else {
      storage.removeItem(EXPIRES_STORAGE_KEY);
    }
  } catch (error) {
    console.warn('[auth] 存储令牌信息失败:', error);
  }
}

function clearStorage() {
  if (!storage) return;
  storage.removeItem(TOKEN_STORAGE_KEY);
  storage.removeItem(REFRESH_STORAGE_KEY);
  storage.removeItem(EXPIRES_STORAGE_KEY);
  storage.removeItem(USER_STORAGE_KEY);
}

const state = () => ({
  token: storage?.getItem(TOKEN_STORAGE_KEY) || '',
  refreshToken: storage?.getItem(REFRESH_STORAGE_KEY) || '',
  expiresAt: Number(storage?.getItem(EXPIRES_STORAGE_KEY)) || 0,
  user: readJson(USER_STORAGE_KEY),
  status: 'idle',
  loading: false,
  error: null
});

const getters = {
  isAuthenticated: (state) => Boolean(state.token),
  authToken: (state) => state.token,
  refreshToken: (state) => state.refreshToken,
  currentUser: (state) => state.user,
  authStatus: (state) => state.status,
  authLoading: (state) => state.loading,
  authError: (state) => state.error,
  isTokenExpired: (state) =>
    state.expiresAt ? Date.now() > Number(state.expiresAt) : true
};

const mutations = {
  SET_TOKENS(state, { token, refreshToken, expiresAt }) {
    state.token = token || '';
    state.refreshToken = refreshToken || '';
    state.expiresAt = expiresAt || 0;
    writeTokens(state);
  },
  SET_USER(state, user) {
    state.user = user || null;
    writeJson(USER_STORAGE_KEY, state.user);
  },
  SET_STATUS(state, status) {
    state.status = status || 'idle';
  },
  SET_LOADING(state, value) {
    state.loading = value;
  },
  SET_ERROR(state, error) {
    state.error = error || null;
  },
  RESET_AUTH(state) {
    state.token = '';
    state.refreshToken = '';
    state.expiresAt = 0;
    state.user = null;
    state.status = 'idle';
    state.loading = false;
    state.error = null;
    clearStorage();
  }
};

const actions = {
  async initialize({ dispatch, getters }) {
    if (getters.isAuthenticated && getters.isTokenExpired) {
      try {
        await dispatch('refreshToken');
      } catch (error) {
        await dispatch('forceLogout');
        throw error;
      }
    }
  },

  async login({ commit, dispatch }, { remember = false, ...credentials }) {
    commit('SET_LOADING', true);
    commit('SET_ERROR', null);
    commit('SET_STATUS', 'authenticating');

    try {
      const { token, refreshToken, expiresAt, user } = await authAPI.login(
        credentials
      );
      commit('SET_TOKENS', { token, refreshToken, expiresAt });
      commit('SET_USER', user);
      commit('SET_STATUS', 'authenticated');
      if (user) {
        await dispatch('user/setProfile', user, { root: true });
      }

      const identifier = (credentials.identifier || credentials.username || '').trim();
      if ((!user || !user.username) && identifier) {
        await dispatch('user/loadProfileFromCache', identifier, { root: true });
      }

      if (remember) {
        writeJson(REMEMBER_STORAGE_KEY, {
          identifier: credentials.identifier
        });
      } else {
        localStorage.removeItem(REMEMBER_STORAGE_KEY);
      }

      return user;
    } catch (error) {
      commit('SET_STATUS', 'error');
      commit('SET_ERROR', error);
      throw error;
    } finally {
      commit('SET_LOADING', false);
    }
  },

  async register({ commit, dispatch }, payload) {
    commit('SET_LOADING', true);
    commit('SET_ERROR', null);
    commit('SET_STATUS', 'authenticating');

    try {
      const { token, refreshToken, expiresAt, user } = await authAPI.register(
        payload
      );
      commit('SET_TOKENS', { token, refreshToken, expiresAt });
      commit('SET_USER', user);
      commit('SET_STATUS', 'authenticated');
      if (user) {
        dispatch('user/setProfile', user, { root: true });
      }
      return user;
    } catch (error) {
      commit('SET_STATUS', 'error');
      commit('SET_ERROR', error);
      throw error;
    } finally {
      commit('SET_LOADING', false);
    }
  },

  async refreshToken({ commit, getters }) {
    const refreshToken = getters.refreshToken || storage?.getItem(REFRESH_STORAGE_KEY);
    if (!refreshToken) {
      throw new Error('缺少刷新令牌');
    }
    try {
      const { token, refreshToken: newRefreshToken, expiresAt } =
        await authAPI.refreshToken(refreshToken);
      commit('SET_TOKENS', {
        token,
        refreshToken: newRefreshToken,
        expiresAt
      });
      commit('SET_STATUS', 'authenticated');
      return token;
    } catch (error) {
      commit('SET_STATUS', 'error');
      commit('SET_ERROR', error);
      throw error;
    }
  },

  async logout({ commit, dispatch }) {
    commit('SET_LOADING', true);
    commit('SET_ERROR', null);
    try {
      await authAPI.logout();
    } catch (error) {
      console.warn('[auth] 退出登录接口调用失败:', error);
    } finally {
      commit('RESET_AUTH');
      dispatch('user/clearProfile', null, { root: true });
      commit('SET_LOADING', false);
    }
  },

  async forceLogout({ commit, dispatch }) {
    commit('RESET_AUTH');
    dispatch('user/clearProfile', null, { root: true });
  },

  updateUser({ commit }, user) {
    commit('SET_USER', user);
  },

  syncTokens({ commit }, payload) {
    if (!payload) {
      commit('RESET_AUTH');
      return;
    }
    commit('SET_TOKENS', payload);
  }
};

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
};

