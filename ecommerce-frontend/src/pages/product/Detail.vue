<template>
  <div class="product-detail-container">
    <el-button text @click="goBack">
      <el-icon><ArrowLeft /></el-icon>
      返回列表
    </el-button>

    <div v-loading="loading" class="detail-content">
      <el-empty v-if="!loading && !product" description="商品不存在" />

      <div v-else class="detail-main">
        <el-card class="product-image-card">
          <el-image
            :src="product.image_url"
            fit="contain"
            class="main-image"
          >
            <template #error>
              <div class="image-slot">
                <el-icon><Picture /></el-icon>
              </div>
            </template>
          </el-image>
        </el-card>

        <el-card class="product-info-card">
          <template #header>
            <div class="card-header">
              <span>商品信息</span>
              <el-tag v-if="product.status === 1" type="success">在售</el-tag>
              <el-tag v-else type="info">已下架</el-tag>
            </div>
          </template>

          <div class="info-content">
            <h1 class="product-title">{{ product.name }}</h1>

            <div class="price-section">
              <span class="price-label">价格</span>
              <span class="price-value">¥{{ formatPrice(product.price) }}</span>
            </div>

            <el-divider />

            <div class="info-row">
              <span class="info-label">商品分类</span>
              <span class="info-value">{{ product.category }}</span>
            </div>

            <div class="info-row">
              <span class="info-label">商品库存</span>
              <span class="info-value" :class="{ 'low-stock': product.stock < 10 }">
                {{ product.stock }} 件
                <el-tag v-if="product.stock < 10" type="warning" size="small">库存紧张</el-tag>
              </span>
            </div>

            <div class="info-row">
              <span class="info-label">上架时间</span>
              <span class="info-value">{{ formatDate(product.created_at) }}</span>
            </div>

            <el-divider />

            <div class="quantity-section">
              <span class="info-label">购买数量</span>
              <el-input-number
                v-model="quantity"
                :min="1"
                :max="product.stock"
                :disabled="product.stock === 0"
              />
            </div>

            <div class="action-section">
              <el-button
                type="primary"
                size="large"
                :disabled="product.stock === 0"
                @click="handleAddToCart"
              >
                加入购物车
              </el-button>
              <el-button size="large" @click="goBack">返回</el-button>
            </div>
          </div>
        </el-card>
      </div>

      <el-card v-if="product" class="description-card">
        <template #header>
          <span>商品详情</span>
        </template>
        <div class="description-content">
          {{ product.description || '暂无详细描述' }}
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useStore } from 'vuex';
import { ElMessage } from 'element-plus';
import { ArrowLeft, Picture } from '@element-plus/icons-vue';

const route = useRoute();
const router = useRouter();
const store = useStore();

const quantity = ref(1);

const product = computed(() => store.getters['product/currentProduct']);
const loading = computed(() => store.getters['product/isLoading']);

function formatPrice(price) {
  return (price / 100).toFixed(2);
}

function formatDate(dateStr) {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function goBack() {
  router.push({ name: 'ProductList' });
}

async function handleAddToCart() {
  try {
    await store.dispatch('cart/addToCart', {
      product: product.value,
      quantity: quantity.value
    });
    ElMessage.success(`已加入购物车 x${quantity.value}`);
  } catch (error) {
    ElMessage.error('加入购物车失败');
  }
}

onMounted(async () => {
  const productId = route.params.id;
  await store.dispatch('product/fetchProductDetail', productId);
});
</script>

<style scoped>
.product-detail-container {
  max-width: 1200px;
  margin: 0 auto;
}

.detail-content {
  margin-top: 16px;
}

.detail-main {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.product-image-card,
.product-info-card {
  height: fit-content;
}

.main-image {
  width: 100%;
  height: 400px;
}

.image-slot {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 400px;
  background: #f5f7fa;
  color: #909399;
  font-size: 64px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.product-title {
  margin: 0 0 20px;
  font-size: 22px;
  color: #303133;
}

.price-section {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.price-label {
  color: #909399;
  font-size: 14px;
}

.price-value {
  font-size: 28px;
  font-weight: 600;
  color: #f56c6c;
}

.info-content {
  padding: 0 8px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.info-label {
  color: #909399;
  font-size: 14px;
}

.info-value {
  color: #303133;
  font-size: 14px;
}

.info-value.low-stock {
  color: #e6a23c;
}

.quantity-section {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.action-section {
  display: flex;
  gap: 12px;
}

.action-section .el-button {
  flex: 1;
}

.description-card {
  margin-top: 24px;
}

.description-content {
  line-height: 1.8;
  color: #606266;
  white-space: pre-wrap;
}

@media (max-width: 768px) {
  .detail-main {
    grid-template-columns: 1fr;
  }
}
</style>
