<template>
  <div class="app-shell">
    <AppSidebar v-if="showLayout" />
    <div class="app-main" :class="{ 'with-layout': showLayout }">
      <AppHeader v-if="showLayout" class="app-header" />
      <div class="app-content">
        <ErrorBoundary>
          <RouterView v-slot="{ Component }">
            <Suspense>
              <component :is="Component" />
              <template #fallback>
                <div class="suspense-fallback">
                  <el-skeleton :rows="4" animated />
                </div>
              </template>
            </Suspense>
          </RouterView>
        </ErrorBoundary>
      </div>
    </div>
    <GlobalStatus />
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { RouterView, useRoute } from 'vue-router';
import ErrorBoundary from './components/common/ErrorBoundary.vue';
import GlobalStatus from './components/common/GlobalStatus.vue';
import AppSidebar from './components/layout/AppSidebar.vue';
import AppHeader from './components/layout/AppHeader.vue';

const route = useRoute();
const showLayout = computed(() => !route.meta?.hideLayout);
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  background: #f3f4f6;
  color: #111827;
  display: flex;
  font-size: clamp(14px, 1.8vw, 16px);
}

.app-main {
  flex: 1;
  padding-right: 12px;
}

.app-main.with-layout {
  margin-left: 12px;
}

.app-header {
  position: sticky;
  top: 0;
  z-index: 10;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(6px);
  border-bottom: 1px solid #e5e7eb;
}

.app-content {
  padding: 24px;
}

.suspense-fallback {
  padding: 24px;
}
</style>

