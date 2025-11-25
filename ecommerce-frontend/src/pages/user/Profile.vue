<template>
  <section class="profile-page">
    <header class="profile-hero">
      <div class="avatar-circle">
        <span>{{ userInfo.initials }}</span>
      </div>
      <div class="hero-content">
        <p class="hero-label">静态个人中心</p>
        <h1>{{ userInfo.name }}</h1>
        <p class="hero-subtitle">
          当前页面展示的是静态示例，不会发起任何接口请求，方便验证登录流程。
          后端接口准备好后，可在此处恢复原来的可编辑表单功能。
        </p>
      </div>
    </header>

    <el-row :gutter="24">
      <el-col :xs="24" :md="14">
        <el-card shadow="hover" class="profile-card">
          <template #header>
            <div class="card-header">
              <span>基础资料</span>
              <el-tag type="success" round effect="light">静态数据</el-tag>
            </div>
          </template>

          <ul class="info-list">
            <li v-for="item in baseInfo" :key="item.label">
              <span class="label">{{ item.label }}</span>
              <span class="value">{{ item.value }}</span>
            </li>
          </ul>

          <el-alert
            title="提示"
            type="info"
            :closable="false"
            description="若需要联调真实接口，可将本页替换回动态表单。"
            show-icon
          />
        </el-card>

        <el-card shadow="hover" class="profile-card">
          <template #header>
            <div class="card-header">
              <span>个人签名</span>
            </div>
          </template>
          <p class="bio-text">
            “保持热爱，持续优化运营体验。” 
          </p>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="10">
        <el-card shadow="hover" class="profile-card">
          <template #header>
            <div class="card-header">
              <span>系统导航</span>
            </div>
          </template>
          <div class="quick-links">
            <el-button type="primary" plain block @click="go('Welcome')">
              欢迎页
            </el-button>
            <el-button plain block @click="go('Navigation')">
              系统导航
            </el-button>
            <el-button plain block @click="go('Dashboard')">
              仪表盘（静态）
            </el-button>
          </div>
        </el-card>

        <el-card shadow="hover" class="profile-card">
          <template #header>
            <div class="card-header">
              <span>退出登录</span>
            </div>
          </template>
          <p class="logout-tip">
            可随时退出并重新登录，以验证后端认证流程。
          </p>
  <el-button type="danger" plain block @click="logout">
    退出当前账号
  </el-button>
        </el-card>
      </el-col>
    </el-row>
  </section>
</template>

<script setup>
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { useStore } from 'vuex';
import { ElMessage } from 'element-plus';

const router = useRouter();
const store = useStore();

const profile = computed(() => store.getters['user/userProfile'] || {});
const fallbackUser = computed(() => store.getters['auth/currentUser'] || {});

const userInfo = computed(() => ({
  name: profile.value.username || fallbackUser.value?.username || '未设置',
  role: fallbackUser.value?.roles?.[0] || '普通用户',
  email: profile.value.email || '未填写',
  phone: profile.value.phone || '未填写',
  joinedAt: profile.value.joinedAt || '未记录',
  initials: (profile.value.username || fallbackUser.value?.username || '访')
    .slice(0, 1)
    .toUpperCase()
}));

const baseInfo = computed(() => [
  { label: '用户名', value: userInfo.value.name },
  { label: '角色', value: userInfo.value.role },
  { label: '邮箱', value: userInfo.value.email },
  { label: '手机号', value: userInfo.value.phone },
  { label: '加入时间', value: userInfo.value.joinedAt }
]);

function go(name) {
  router.push({ name }).catch(() => {});
}

async function logout() {
  await store.dispatch('auth/logout');
  ElMessage.success('已退出登录');
  router.replace({ name: 'Login' });
}
</script>

<style scoped>
.profile-page {
  min-height: calc(100vh - 80px);
  padding: 24px;
  background: #f5f7fb;
}

.profile-hero {
  display: flex;
  gap: 20px;
  align-items: center;
  padding: 24px;
  border-radius: 16px;
  background: radial-gradient(circle at top left, #c7d2fe, #eef2ff);
  margin-bottom: 20px;
}

.avatar-circle {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: #312e81;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 600;
}

.hero-label {
  margin: 0;
  font-size: 13px;
  color: #4c1d95;
  letter-spacing: 1px;
}

.hero-content h1 {
  margin: 4px 0;
  font-size: 28px;
  color: #1e1b4b;
}

.hero-subtitle {
  margin: 0;
  color: #4c1d95;
  max-width: 560px;
}

.profile-card {
  border-radius: 18px;
  margin-bottom: 24px;
  border: none;
  transition: transform 0.35s ease, box-shadow 0.35s ease;
}

.profile-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 18px 45px rgba(31, 41, 55, 0.15);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  color: #111827;
  font-size: 15px;
}

.info-list {
  list-style: none;
  margin: 0 0 16px;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-list li {
  display: flex;
  justify-content: space-between;
  color: #374151;
}

.info-list .label {
  color: #6b7280;
}

.bio-text {
  margin: 0;
  line-height: 1.8;
  color: #4b5563;
  font-size: 15px;
}

.quick-links :deep(.el-button) {
  margin-bottom: 10px;
}

.logout-tip {
  margin: 0 0 12px;
  color: #6b7280;
}

@media (max-width: 768px) {
  .profile-page {
    padding: 16px;
  }
  .profile-hero {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>

