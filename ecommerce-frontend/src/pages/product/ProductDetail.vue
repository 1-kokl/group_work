<template>
  <section class="product-detail-page">
    <div class="back-button">
      <el-button text @click="goBack">
        <el-icon><ArrowLeft /></el-icon> 返回商品列表
      </el-button>
    </div>

    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>

    <div v-else-if="product" class="product-content">
      <el-card class="product-card" shadow="hover">
        <div class="product-grid">
          <div class="product-image-section">
            <div v-if="product.image_url" class="main-image">
              <img :src="getImageUrl(product.image_url)" :alt="product.name" />
            </div>
            <el-empty v-else description="暂无图片" :image-size="200" />
          </div>

          <div class="product-info-section">
            <div class="product-header">
              <h1 class="product-title">{{ product.name }}</h1>
              <el-tag :type="product.status ? 'success' : 'info'" size="large">
                {{ product.status ? '在售' : '已下架' }}
              </el-tag>
            </div>

            <div class="product-meta">
              <el-tag type="info" effect="plain">
                <el-icon><InfoFilled /></el-icon>
                商品ID: {{ product.id }}
              </el-tag>
              <el-tag v-if="product.category" type="warning" effect="plain">
                <el-icon><Collection /></el-icon>
                分类: {{ product.category }}
              </el-tag>
            </div>

            <div class="product-price">
              <span class="price-label">价格：</span>
              <span class="price-value">¥{{ product.price.toFixed(2) }}</span>
            </div>

            <div class="product-stock">
              <span class="stock-label">库存：</span>
              <span :class="product.stock > 0 ? 'stock-available' : 'stock-unavailable'">
                {{ product.stock > 0 ? `剩余 ${product.stock} 件` : '暂时缺货' }}
              </span>
            </div>

            <div class="product-seller">
              <span class="seller-label">卖家：</span>
              <span class="seller-name">{{ product.seller_username || '未知' }}</span>
            </div>

            <div class="product-time">
              <el-text type="info" size="small">
                上架时间：{{ formatDate(product.created_at) }}
              </el-text>
            </div>

            <div class="action-buttons">
              <el-button
                type="primary"
                size="large"
                :disabled="!product.status || product.stock === 0"
                @click="addToCart"
              >
                <el-icon><ShoppingCart /></el-icon>
                加入购物车
              </el-button>

              <el-button
                :type="isFavorited ? 'danger' : 'default'"
                size="large"
                @click="toggleFavorite"
              >
                <el-icon><StarFilled v-if="isFavorited" /><Star v-else /></el-icon>
                {{ isFavorited ? '已收藏' : '收藏' }}
              </el-button>
            </div>

            <el-alert
              v-if="!product.status"
              title="该商品已下架"
              type="warning"
              :closable="false"
              show-icon
              style="margin-top: 20px"
            />

            <el-alert
              v-else-if="product.stock === 0"
              title="该商品暂时缺货"
              type="info"
              :closable="false"
              show-icon
              style="margin-top: 20px"
            />
          </div>
        </div>

        <el-divider />

        <div class="product-description">
          <h3>商品描述</h3>
          <p>{{ product.description || '暂无描述' }}</p>
        </div>
      </el-card>
    </div>

    <el-empty v-else description="商品不存在" />
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  ShoppingCart,
  Star,
  StarFilled,
  InfoFilled,
  Collection
} from '@element-plus/icons-vue'
import http from '@/services/http'

const route = useRoute()
const router = useRouter()
const store = useStore()

const loading = ref(false)
const product = ref(null)
const isFavorited = ref(false)

const productId = route.params.id

const fetchProductDetail = async () => {
  loading.value = true
  try {
    const res = await http.get(`/api/ecommerce/products/${productId}`)
    const responseData = res.data || res

    if (responseData.code === 200) {
      product.value = responseData.data
      checkFavorite()
    } else {
      ElMessage.error(responseData.msg || '获取商品详情失败')
    }
  } catch (error) {
    console.error('加载商品详情失败:', error)
    ElMessage.error('网络错误，请检查后端服务是否启动')
  } finally {
    loading.value = false
  }
}

const checkFavorite = async () => {
  try {
    const userId = store.getters['auth/currentUser']?.id
    if (!userId) return

    const res = await http.get(`/api/ecommerce/favorites/${productId}`)
    const responseData = res.data || res

    if (responseData.code === 200) {
      isFavorited.value = responseData.data.is_favorited || false
    }
  } catch (error) {
    console.error('检查收藏状态失败:', error)
  }
}

const addToCart = async () => {
  try {
    const res = await http.post('/api/ecommerce/cart', {
      product_id: productId,
      quantity: 1
    })

    const responseData = res.data || res

    if (responseData.code === 200) {
      ElMessage.success('已添加到购物车')
    } else {
      ElMessage.error(responseData.msg || '添加失败')
    }
  } catch (error) {
    console.error('添加到购物车失败:', error)
    ElMessage.error('添加失败：' + (error.message || '未知错误'))
  }
}

const toggleFavorite = async () => {
  try {
    const url = isFavorited.value
      ? `/api/ecommerce/favorites/${productId}`
      : '/api/ecommerce/favorites'

    const method = isFavorited.value ? 'delete' : 'post'

    const res = await http[method](url, isFavorited.value ? null : { product_id: productId })
    const responseData = res.data || res

    if (responseData.code === 200) {
      isFavorited.value = !isFavorited.value
      ElMessage.success(isFavorited.value ? '收藏成功' : '已取消收藏')
    } else {
      ElMessage.error(responseData.msg || '操作失败')
    }
  } catch (error) {
    console.error('收藏操作失败:', error)
    ElMessage.error('操作失败：' + (error.message || '未知错误'))
  }
}

const getImageUrl = (imageUrl) => {
  if (!imageUrl) return ''
  if (imageUrl.startsWith('http')) return imageUrl
  const baseUrl = process.env.VUE_APP_API_BASE_URL || 'http://localhost:5000'
  return `${baseUrl}${imageUrl}`
}

const formatDate = (dateString) => {
  if (!dateString) return '未知'
  return new Date(dateString).toLocaleString('zh-CN')
}

const goBack = () => {
  router.push({ name: 'Products' })
}

onMounted(() => {
  fetchProductDetail()
})
</script>

<style scoped>
.product-detail-page {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.back-button {
  margin-bottom: 20px;
}

.loading-container {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
}

.product-card {
  border-radius: 12px;
}

.product-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 40px;
}

.product-image-section {
  display: flex;
  align-items: center;
  justify-content: center;
}

.main-image {
  width: 100%;
  max-width: 500px;
  aspect-ratio: 1;
  border-radius: 12px;
  overflow: hidden;
  background: #f5f5f5;
}

.main-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.product-info-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.product-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.product-title {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}

.product-meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.product-price {
  padding: 16px;
  background: linear-gradient(135deg, #fff5f5 0%, #ffe5e5 100%);
  border-radius: 8px;
}

.price-label {
  font-size: 16px;
  color: #606266;
}

.price-value {
  font-size: 32px;
  font-weight: bold;
  color: #f56c6c;
  margin-left: 8px;
}

.product-stock {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.stock-label {
  font-size: 14px;
  color: #606266;
}

.stock-available {
  color: #67c23a;
  font-weight: 500;
}

.stock-unavailable {
  color: #f56c6c;
  font-weight: 500;
}

.product-seller {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.seller-label {
  font-size: 14px;
  color: #606266;
}

.seller-name {
  color: #409eff;
  font-weight: 500;
}

.product-time {
  color: #909399;
}

.action-buttons {
  display: flex;
  gap: 16px;
  margin-top: 10px;
}

.action-buttons .el-button {
  flex: 1;
}

.product-description {
  margin-top: 20px;
}

.product-description h3 {
  margin: 0 0 12px;
  font-size: 18px;
  color: #303133;
}

.product-description p {
  margin: 0;
  line-height: 1.8;
  color: #606266;
  white-space: pre-wrap;
}

@media (max-width: 768px) {
  .product-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .product-title {
    font-size: 22px;
  }

  .price-value {
    font-size: 24px;
  }

  .action-buttons {
    flex-direction: column;
  }
}
</style>
