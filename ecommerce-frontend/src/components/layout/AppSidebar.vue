<template>
  <aside
    :class="['app-sidebar', { 'is-expanded': isExpanded }]"
    @mouseenter="setHover(true)"
    @mouseleave="setHover(false)"
  >
    <div class="sidebar-content">
      <div class="sidebar-brand">
        <el-icon><Grid /></el-icon>
        <span v-if="isExpanded">管理菜单</span>
      </div>

      <div class="sidebar-user" v-if="isExpanded">
        <div class="user-avatar">{{ userInitials }}</div>
        <div class="user-meta">
          <strong>{{ userName }}</strong>
          <small>{{ userRole }}</small>
        </div>
      </div>

      <el-menu
        :default-active="activeRoute"
        class="sidebar-menu"
        background-color="transparent"
        text-color="#6b7280"
        active-text-color="#2563eb"
      >
        <el-menu-item
          v-for="item in visibleMenus"
          :key="item.name"
          :index="item.name"
          @click="() => navigate(item)"
        >
          <el-icon v-if="item.icon"><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-actions" v-if="isExpanded">
        <el-button type="primary" plain block size="small" @click="goProfile">
          个人中心
        </el-button>
        <el-button type="danger" plain block size="small" @click="logout">
          退出登录
        </el-button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useStore } from 'vuex';
import { Grid, Histogram, User, Menu as MenuIcon } from '@element-plus/icons-vue';
import { sanitizeInput } from '../../utils/security';

const router = useRouter();
const route = useRoute();
const store = useStore();
const hover = ref(false);
const isExpanded = computed(() => hover.value);

function setHover(value) {
  hover.value = value;
}

const navMenus = [
  {
    name: 'Dashboard',
    label: '仪表盘总览',
    icon: Histogram,
    roles: ['admin', 'operator', 'merchant']
  },
  {
    name: 'Profile',
    label: '个人中心',
    icon: User
  },
  {
    name: 'Navigation',
    label: '系统导航',
    icon: MenuIcon
  }
];

const profileState = computed(() => store.getters['user/userProfile'] || {});
const userState = computed(() => store.getters['auth/currentUser'] || {});
const userRoles = computed(() => userState.value.roles || []);

const userName = computed(
  () =>
    sanitizeInput(
      profileState.value.username ||
        userState.value.username ||
        '未设置'
    )
);
const userRole = computed(() => userRoles.value[0] || '普通用户');
const userInitials = computed(() =>
  userName.value ? userName.value.slice(0, 1).toUpperCase() : 'U'
);

const visibleMenus = computed(() =>
  navMenus.filter((item) => {
    if (!item.roles?.length) return true;
    return item.roles.some((role) => userRoles.value.includes(role));
  })
);

const activeRoute = computed(() => route.name);

function navigate(item) {
  router.push({ name: item.name }).catch(() => {});
}

function goProfile() {
  router.push({ name: 'Profile' }).catch(() => {});
}

async function logout() {
  await store.dispatch('auth/logout');
  await store.dispatch('user/clearProfile');
  router.replace({ name: 'Login' });
}
</script>

<style scoped>
.app-sidebar {
  position: fixed;
  top: 70px;
  left: 0;
  height: calc(100vh - 70px);
  width: 12px;
  z-index: 900;
  pointer-events: auto;
}

.app-sidebar::before {
  content: '';
  width: 12px;
  background: linear-gradient(180deg, rgba(79, 70, 229, 0.9), rgba(59, 130, 246, 0.95));
  border-radius: 0 6px 6px 0;
  box-shadow: 4px 0 14px rgba(59, 130, 246, 0.35);
  cursor: pointer;
}

.sidebar-content {
  position: absolute;
  top: 0;
  left: 0;
  height: calc(100vh - 70px);
  width: 240px;
  background: rgba(15, 23, 42, 0.94);
  backdrop-filter: blur(10px);
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  padding: 18px 14px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  transform: translateX(-105%);
  transition: transform 0.3s ease;
  box-shadow: 12px 0 30px rgba(15, 23, 42, 0.45);
  pointer-events: auto;
}

.app-sidebar.is-expanded .sidebar-content {
  transform: translateX(0);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 600;
  color: #fff;
  padding: 0 8px;
}

.sidebar-user {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 8px 4px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.user-avatar {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: rgba(59, 130, 246, 0.35);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 18px;
}

.user-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  color: #fff;
}

.user-meta small {
  color: rgba(255, 255, 255, 0.7);
}

.sidebar-menu {
  border-right: none;
}

.sidebar-menu :deep(.el-menu-item) {
  border-radius: 10px;
  margin-bottom: 8px;
  color: rgba(255, 255, 255, 0.7);
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background: rgba(255, 255, 255, 0.18);
  font-weight: 600;
  color: #fff;
}

.sidebar-actions {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.app-sidebar::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: 0 20px 20px 0;
  box-shadow: inset 0 0 20px rgba(255, 255, 255, 0.05);
}

@media (max-width: 1024px) {
  .app-sidebar {
    display: none;
  }
}
</style>

