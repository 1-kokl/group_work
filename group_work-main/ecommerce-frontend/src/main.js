import { createApp } from 'vue';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';

import App from './App.vue';
import router from './router';
import store from './store';

async function startMockWorkerIfNeeded() {
  if (process.env.VUE_APP_USE_MSW === 'true') {
    const { worker } = await import('./mocks/browser');
    await worker.start({
      onUnhandledRequest: 'bypass'
    });
    // eslint-disable-next-line no-console
    console.info('[MSW] Mock service worker started.');
  }
}

async function bootstrap() {
  await startMockWorkerIfNeeded();

  const app = createApp(App);
  app.use(store);
  app.use(router);
  app.use(ElementPlus);
  app.mount('#app');

  if (typeof window !== 'undefined') {
    window.addEventListener('beforeunload', () => {
      store.dispatch('auth/forceLogout');
    });
  }
}

bootstrap();

