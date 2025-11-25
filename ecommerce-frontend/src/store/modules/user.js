import userAPI, { invalidateUserCaches } from '../../services/api/userAPI';

const sessionStore = typeof window !== 'undefined' ? window.sessionStorage : null;
const persistentStore = typeof window !== 'undefined' ? window.localStorage : null;
const PROFILE_STORAGE_KEY = 'user.profile';
const SETTINGS_STORAGE_KEY = 'user.settings';
const PROFILE_CACHE_PREFIX = 'user.profile.cache:';

function readJson(key) {
  try {
    if (!sessionStore) return null;
    const raw = sessionStore.getItem(key);
    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    console.warn(`[user] 读取 ${key} 失败:`, error);
    return null;
  }
}

function writeJson(key, value) {
  try {
    if (!sessionStore) return;
    if (value === null || value === undefined) {
      sessionStore.removeItem(key);
    } else {
      sessionStore.setItem(key, JSON.stringify(value));
    }
  } catch (error) {
    console.warn(`[user] 写入 ${key} 失败:`, error);
  }
}

const state = () => ({
  profile: readJson(PROFILE_STORAGE_KEY),
  settings: readJson(SETTINGS_STORAGE_KEY) || {},
  lastFetchedAt: null,
  loading: false,
  error: null
});

const getters = {
  userProfile: (state) => state.profile,
  userSettings: (state) => state.settings,
  profileLoaded: (state) => Boolean(state.profile),
  profileLastFetchedAt: (state) => state.lastFetchedAt,
  userLoading: (state) => state.loading,
  userError: (state) => state.error
};

const mutations = {
  SET_PROFILE(state, profile) {
    state.profile = profile || null;
    writeJson(PROFILE_STORAGE_KEY, state.profile);
  },
  SET_SETTINGS(state, settings) {
    state.settings = settings || {};
    writeJson(SETTINGS_STORAGE_KEY, state.settings);
  },
  SET_LAST_FETCHED_AT(state, timestamp) {
    state.lastFetchedAt = timestamp || null;
  },
  SET_LOADING(state, value) {
    state.loading = value;
  },
  SET_ERROR(state, error) {
    state.error = error || null;
  },
  RESET_PROFILE(state) {
    state.profile = null;
    state.settings = {};
    state.lastFetchedAt = null;
    state.loading = false;
    state.error = null;
    sessionStore?.removeItem(PROFILE_STORAGE_KEY);
    sessionStore?.removeItem(SETTINGS_STORAGE_KEY);
  }
};

function persistProfileCache(profile) {
  if (!persistentStore || !profile?.username) return;
  try {
    persistentStore.setItem(
      `${PROFILE_CACHE_PREFIX}${profile.username}`,
      JSON.stringify(profile)
    );
  } catch (error) {
    console.warn('[user] 写入本地缓存失败:', error);
  }
}

function readProfileCache(username) {
  if (!persistentStore || !username) return null;
  try {
    const raw = persistentStore.getItem(`${PROFILE_CACHE_PREFIX}${username}`);
    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    console.warn('[user] 读取本地缓存失败:', error);
    return null;
  }
}

const actions = {
  setProfile({ commit }, profile) {
    commit('SET_PROFILE', profile);
    commit('SET_LAST_FETCHED_AT', Date.now());
    persistProfileCache(profile);
  },

  setSettings({ commit }, settings) {
    commit('SET_SETTINGS', settings);
  },

  async fetchProfile({ commit, state }, { force = false } = {}) {
    if (!force && state.profile) {
      return state.profile;
    }

    commit('SET_LOADING', true);
    commit('SET_ERROR', null);

    try {
      const profile = await userAPI.getProfile({ force });
      commit('SET_PROFILE', profile);
      commit('SET_LAST_FETCHED_AT', Date.now());
      return profile;
    } catch (error) {
      commit('SET_ERROR', error);
      throw error;
    } finally {
      commit('SET_LOADING', false);
    }
  },

  async updateProfile({ commit, dispatch, state }, payload) {
    commit('SET_LOADING', true);
    commit('SET_ERROR', null);

    try {
      await userAPI.updateProfile(payload);
      const nextProfile = {
        ...(state.profile || {}),
        ...payload
      };
      commit('SET_PROFILE', nextProfile);
      commit('SET_LAST_FETCHED_AT', Date.now());
      dispatch('auth/updateUser', nextProfile, { root: true });
      return nextProfile;
    } catch (error) {
      commit('SET_ERROR', error);
      throw error;
    } finally {
      commit('SET_LOADING', false);
    }
  },

  async changePassword({ commit }, payload) {
    commit('SET_LOADING', true);
    commit('SET_ERROR', null);
    try {
      await userAPI.changePassword(payload);
    } catch (error) {
      commit('SET_ERROR', error);
      throw error;
    } finally {
      commit('SET_LOADING', false);
    }
  },

  async fetchDevices() {
    return userAPI.getDevices();
  },

  clearProfile({ commit }) {
    commit('RESET_PROFILE');
    invalidateUserCaches();
  },

  loadProfileFromCache({ commit }, username) {
    const cached = readProfileCache(username);
    if (cached) {
      commit('SET_PROFILE', cached);
      commit('SET_LAST_FETCHED_AT', Date.now());
    }
    return cached;
  }
};

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
};

