<template>
  <nav class="mobile-nav">
    <button
      v-for="item in visibleMenus"
      :key="item.name"
      :class="['mobile-nav-item', { active: activeRoute === item.name }]"
      @click="() => navigate(item)"
    >
      <el-icon><component :is="item.icon" /></el-icon>
      <span>{{ item.label }}</span>
    </button>
  </nav>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useStore } from 'vuex';
import { Histogram, User } from '@element-plus/icons-vue';

const router = useRouter();
const route = useRoute();
const store = useStore();

const navMenus = [
  {
    name: 'Dashboard',
    label: '概览',
    icon: Histogram,
    roles: ['admin', 'operator', 'merchant']
  },
  {
    name: 'Profile',
    label: '我的',
    icon: User,
    roles: ['admin', 'operator', 'merchant']
  }
];

const roles = computed(() => store.getters['auth/currentUser']?.roles || []);

const visibleMenus = computed(() =>
  navMenus.filter((item) => {
    if (!item.roles?.length) return true;
    return item.roles.some((role) => roles.value.includes(role));
  })
);

const activeRoute = computed(() => route.name);

function navigate(item) {
  router.push({ name: item.name }).catch(() => {});
}
</script>

<style scoped>
.mobile-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #ffffffee;
  backdrop-filter: blur(12px);
  border-top: 1px solid #e5e7eb;
  display: none;
  align-items: center;
  justify-content: space-around;
  padding: 8px 0;
  z-index: 110;
}

.mobile-nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  font-size: 12px;
  color: #6b7280;
  border: none;
  background: transparent;
}

.mobile-nav-item.active {
  color: #2563eb;
}

@media (max-width: 768px) {
  .mobile-nav {
    display: flex;
  }
}
</style>

