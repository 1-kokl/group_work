<template>
  <div class="global-status">
    <LoadingOverlay :visible="globalLoading" :message="loadingMessage" />

    <transition name="slide-fade">
      <el-alert
        v-if="visibleError"
        class="global-error"
        type="error"
        :closable="true"
        show-icon
        :title="visibleError.message || '请求发生错误，请稍后再试。'"
        @close="handleClose"
      />
    </transition>
  </div>
</template>

<script setup>
import { computed, ref, watch, onBeforeUnmount } from 'vue';
import { useStore } from 'vuex';
import LoadingOverlay from './LoadingOverlay.vue';

const store = useStore();

const globalLoading = computed(() => store.getters.globalLoading);
const globalError = computed(() => store.getters.globalError);
const loadingMessage = computed(() =>
  globalLoading.value ? '正在同步最新数据，请稍候…' : ''
);

const visibleError = ref(null);
let hideTimer = null;

function startAutoHide() {
  if (hideTimer) clearTimeout(hideTimer);
  hideTimer = setTimeout(() => {
    handleClose();
  }, 5000);
}

function handleClose() {
  visibleError.value = null;
  store.commit('SET_GLOBAL_ERROR', null);
}

watch(
  globalError,
  (error) => {
    if (!error) {
      handleClose();
      return;
    }
    visibleError.value = {
      message: error.message,
      code: error.code,
      status: error.status
    };
    startAutoHide();
  },
  { immediate: true }
);

onBeforeUnmount(() => {
  if (hideTimer) clearTimeout(hideTimer);
});
</script>

<style scoped>
.global-error {
  position: fixed;
  top: 88px;
  right: 16px;
  width: min(360px, calc(100vw - 32px));
  z-index: 1300;
}

.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.25s ease;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}
</style>

