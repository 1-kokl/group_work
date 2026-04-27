<template>
  <section class="nav-page">
    <header class="nav-hero">
      <h1>系统导航</h1>
      <p>静态导航示例，汇集常用入口，帮助快速验证路由是否可用。</p>
    </header>

    <el-row :gutter="24">
      <el-col
        :xs="24"
        :md="12"
        v-for="section in sections"
        :key="section.title"
      >
        <el-card shadow="hover" :class="['nav-card', section.theme]">
          <template #header>
            <div class="card-header">
              <el-icon><component :is="section.icon" /></el-icon>
              <span>{{ section.title }}</span>
            </div>
          </template>

          <p class="card-desc">{{ section.desc }}</p>
          <el-button type="primary" plain @click="go(section.route)">
            前往 {{ section.button }}
          </el-button>
        </el-card>
      </el-col>
    </el-row>
  </section>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { Menu, ShoppingCart, Goods, Document, UserFilled } from '@element-plus/icons-vue';

const router = useRouter();

const sections = [
  {
    title: '商品列表',
    desc: '浏览和搜索商品，查看商品详情。',
    icon: Goods,
    route: 'ProductList',
    button: '商品列表',
    theme: 'theme-blue'
  },
  {
    title: '购物车',
    desc: '管理购物车中的商品，进行结算。',
    icon: ShoppingCart,
    route: 'Cart',
    button: '购物车',
    theme: 'theme-green'
  },
  {
    title: '我的订单',
    desc: '查看订单列表和订单详情。',
    icon: Document,
    route: 'OrderList',
    button: '订单列表',
    theme: 'theme-purple'
  },
  {
    title: '个人中心',
    desc: '查看和编辑个人资料信息。',
    icon: UserFilled,
    route: 'Profile',
    button: '个人中心',
    theme: 'theme-orange'
  }
];

function go(name) {
  router.push({ name }).catch(() => {});
}
</script>

<style scoped>
.nav-page {
  padding: 24px;
  min-height: calc(100vh - 80px);
  background: #f9fafb;
}

.nav-hero {
  margin-bottom: 20px;
}

.nav-hero h1 {
  margin: 0 0 8px;
  font-size: 28px;
  color: #1f2937;
}

.nav-hero p {
  margin: 0;
  color: #6b7280;
}

.nav-card {
  border-radius: 18px;
  margin-bottom: 24px;
  border: none;
  transition: transform 0.35s ease, box-shadow 0.35s ease;
  position: relative;
  overflow: hidden;
}

.nav-card::after {
  content: '';
  position: absolute;
  inset: 0;
  opacity: 0.08;
  background: linear-gradient(135deg, #fff, transparent 60%);
  pointer-events: none;
}

.nav-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 18px 45px rgba(31, 41, 55, 0.15);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  color: #fff;
}

.card-header :deep(.el-icon) {
  font-size: 20px;
}

.card-desc {
  color: rgba(255, 255, 255, 0.85);
  min-height: 48px;
  margin-bottom: 20px;
}

.nav-card.theme-purple {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
}

.nav-card.theme-green {
  background: linear-gradient(135deg, #10b981, #34d399);
  color: #fff;
}

.nav-card.theme-blue {
  background: linear-gradient(135deg, #0ea5e9, #3b82f6);
  color: #fff;
}

.nav-card.theme-orange {
  background: linear-gradient(135deg, #f59e0b, #f97316);
  color: #fff;
}

.nav-card.theme-red {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: #fff;
}

.nav-card :deep(.el-button) {
  border-color: rgba(255, 255, 255, 0.7);
  color: #fff;
  background-color: rgba(255, 255, 255, 0.15);
}

.nav-card :deep(.el-button:hover) {
  border-color: #fff;
  background-color: rgba(255, 255, 255, 0.3);
}
</style>

