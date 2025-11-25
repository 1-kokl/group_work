import { createStore } from 'vuex';
import auth from './modules/auth';
import user from './modules/user';

function createAuthCleanupPlugin() {
  return (store) => {
    store.subscribe((mutation) => {
      if (mutation.type === 'auth/RESET_AUTH') {
        store.commit('user/RESET_PROFILE');
      }
    });
  };
}

function createEventBridgePlugin() {
  return (store) => {
    if (typeof window === 'undefined') return;

    window.addEventListener('auth:token-refreshed', (event) => {
      if (!event?.detail) return;
      store.dispatch('auth/syncTokens', event.detail);
      store.commit('auth/SET_STATUS', 'authenticated');
    });

    window.addEventListener('auth:token-expired', () => {
      store.dispatch('auth/forceLogout');
    });

    window.addEventListener('http:loading', (event) => {
      store.commit('SET_GLOBAL_LOADING', Boolean(event?.detail));
    });

    window.addEventListener('http:error', (event) => {
      const detail = event?.detail;
      if (!detail || detail.suppressGlobalError) {
        return;
      }
      store.commit('SET_GLOBAL_ERROR', detail);
    });
  };
}

const store = createStore({
  state: () => ({
    globalLoading: false,
    globalError: null
  }),
  getters: {
    globalLoading: (state) => state.globalLoading,
    globalError: (state) => state.globalError
  },
  mutations: {
    SET_GLOBAL_LOADING(state, value) {
      state.globalLoading = Boolean(value);
    },
    SET_GLOBAL_ERROR(state, error) {
      state.globalError = error || null;
    }
  },
  modules: {
    auth,
    user
  },
  strict: process.env.NODE_ENV !== 'production',
  plugins: [createAuthCleanupPlugin(), createEventBridgePlugin()]
});

export default store;

