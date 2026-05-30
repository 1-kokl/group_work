<template>
  <section class="profile-page">
    <header class="profile-hero">
      <div class="avatar-circle">
        <span>{{ userInfo.initials }}</span>
      </div>
      <div class="hero-content">
        <p class="hero-label">个人中心</p>
        <h1>{{ userInfo.name }}</h1>
        <p class="hero-subtitle">
          管理您的个人资料以及上架的商品信息。
        </p>
      </div>
    </header>

    <!-- 使用 Tabs 切换不同功能模块 -->
    <el-tabs v-model="activeTab" class="profile-tabs">
      <!-- 标签 1: 基础资料 (保留原有逻辑) -->
      <el-tab-pane label="👤 基础资料" name="info">
        <el-row :gutter="24">
          <el-col :xs="24" :md="14">
            <el-card shadow="hover" class="profile-card">
              <template #header>
                <div class="card-header">
                  <span>个人信息</span>
                </div>
              </template>
              <ul class="info-list">
                <li v-for="item in baseInfo" :key="item.label">
                  <span class="label">{{ item.label }}</span>
                  <span class="value">{{ item.value }}</span>
                </li>
              </ul>
            </el-card>
          </el-col>
          <el-col :xs="24" :md="10">
             <el-card shadow="hover" class="profile-card">
              <template #header><span>系统导航</span></template>
              <div class="quick-links">
                <el-button type="primary" plain block @click="go('Dashboard')">
                  🛍️ 商品管理中心
                </el-button>
                <el-button type="success" plain block @click="go('Orders')">
                  📦 我的订单
                </el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- 标签 2: 我的商品 (新增功能) -->
      <el-tab-pane label="📦 我的商品" name="products">
        <div class="product-manager">
          <div class="manager-header">
            <h3>我已上架的商品</h3>
            <el-button type="primary" @click="go('Dashboard')">+ 去添加新商品</el-button>
          </div>

          <el-table v-if="myProducts.length > 0" :data="myProducts" style="width: 100%" border>
            <el-table-column prop="name" label="商品名称" width="180" />
            <el-table-column prop="price" label="价格">
              <template #default="scope">¥{{ scope.row.price.toFixed(2) }}</template>
            </el-table-column>
            <el-table-column prop="description" label="描述" show-overflow-tooltip />
            <el-table-column prop="created_at" label="上架时间" width="180" />
          </el-table>

          <el-empty v-else description="您还没有上架任何商品，快去 Dashboard 添加吧！" />
        </div>
      </el-tab-pane>

    </el-tabs>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useStore } from 'vuex';
import axios from 'axios';
import { ElMessage } from 'element-plus';

const router = useRouter();
const store = useStore();
const activeTab = ref('info'); // 默认显示基础资料
const myProducts = ref([]);

// --- 原有用户信息逻辑 ---
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

// --- 新增：获取我的商品逻辑 ---
const fetchMyProducts = async () => {
  try {
    const token = localStorage.getItem('token');
    if (!token) return;
    const res = await axios.get('http://localhost:5000/api/my-products', {
      headers: { Authorization: `Bearer ${token}` }
    });

    if (res.data.code === 200) {
      myProducts.value = res.data.data;
    }
  } catch (error) {
    console.error('获取我的商品失败:', error);
  }
};

// 监听标签切换，如果切换到“我的商品”则加载数据
const handleTabChange = (tabName) => {
  if (tabName === 'products') {
    fetchMyProducts();
  }
};
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

.hero-content h1 { margin: 4px 0; font-size: 28px; color: #1e1b4b; }
.hero-subtitle { margin: 0; color: #4c1d95; }

.profile-tabs {
  background: #fff;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.profile-card {
  border-radius: 12px;
  margin-bottom: 24px;
}

.info-list { list-style: none; padding: 0; }
.info-list li { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }
.info-list .label { color: #666; }

.manager-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.quick-links .el-button { margin-bottom: 10px; }
</style>
