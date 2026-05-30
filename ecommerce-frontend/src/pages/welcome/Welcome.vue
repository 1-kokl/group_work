<template>
  <section class="welcome-page">
    <div class="welcome-card">
      <h1>登录成功 🎉</h1>
      <p class="welcome-tip">
        您已成功通过后端认证。此页面只展示静态内容，不会再调用任何接口，
        方便快速验证后端的登录/注册接口是否可用。
      </p>

      <div class="token-info" v-if="token">
        <span class="label">当前令牌：</span>
        <code>{{ token }}</code>
      </div>

      <div class="actions">
        <el-button type="primary" @click="goDashboard">进入仪表盘</el-button>
        <el-button @click="logout">退出登录</el-button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { useStore } from 'vuex';
import { ElMessage } from 'element-plus';

const router = useRouter();
const store = useStore();

const token = computed(() => store.getters['auth/authToken']);

function goDashboard() {
  router.push({ name: 'Dashboard' });
}

async function logout() {
  await store.dispatch('auth/logout');
  ElMessage.success('已退出登录');
  router.replace({ name: 'Login' });
}
</script>

<style scoped>
.welcome-page {
  min-height: 70vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  background: linear-gradient(135deg, #ecfdf5 0%, #ffffff 100%);
}

.welcome-card {
  width: min(520px, 100%);
  background: #fff;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 25px 60px rgba(15, 23, 42, 0.12);
  text-align: center;
}

.welcome-card h1 {
  margin: 0 0 12px;
  font-size: 28px;
  color: #111827;
}

.welcome-tip {
  margin: 0 auto 20px;
  color: #4b5563;
  line-height: 1.6;
}

.token-info {
  margin: 0 auto 24px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
  word-break: break-all;
  text-align: left;
  font-family: 'Fira Code', Consolas, monospace;
  font-size: 13px;
}

.token-info .label {
  font-weight: 600;
  color: #374151;
}

.actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}
</style>

