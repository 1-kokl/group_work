<template>
  <transition name="fade">
    <div v-if="visible" class="loading-overlay" role="alert" aria-live="assertive">
      <div class="spinner">
        <span class="spinner-dot" />
        <span class="spinner-dot" />
        <span class="spinner-dot" />
      </div>
      <p class="loading-text">{{ message }}</p>
    </div>
  </transition>
</template>

<script setup>
defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  message: {
    type: String,
    default: '正在加载数据，请稍候...'
  }
});
</script>

<style scoped>
.loading-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1200;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(8px);
  padding: 24px;
  text-align: center;
}

.spinner {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.spinner-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: linear-gradient(135deg, #2563eb, #38bdf8);
  animation: bounce 1.2s infinite ease-in-out;
}

.spinner-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.spinner-dot:nth-child(3) {
  animation-delay: 0.4s;
}

.loading-text {
  color: #1f2937;
  font-size: clamp(14px, 2vw, 16px);
  margin: 0;
}

@keyframes bounce {
  0%,
  80%,
  100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

