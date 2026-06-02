<template>
  <section class="my-products-page">
    <header class="page-header">
      <h1>📦 我的上架商品</h1>
      <p>管理您在平台上架的所有商品</p>
    </header>

    <div class="action-bar">
      <el-button type="primary" @click="goToProductCenter">
        <el-icon><Plus /></el-icon> 上架新商品
      </el-button>
      <el-button @click="fetchMyProducts">
        <el-icon><Refresh /></el-icon> 刷新列表
      </el-button>
      <el-button :type="showAll ? 'primary' : 'default'" @click="toggleShowAll">
        {{ showAll ? '只看上架' : '显示全部' }}
      </el-button>
    </div>

    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="3" animated />
    </div>

    <div v-else class="product-grid">
      <el-card v-for="product in products" :key="product.id" class="product-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="product-name">{{ product.name }}</span>
            <el-tag :type="product.status ? 'success' : 'info'" size="small">
              {{ product.status ? '上架中' : '已下架' }}
            </el-tag>
          </div>
        </template>
        <div class="product-body">
          <div v-if="product.image_url" class="product-image">
            <img :src="getImageUrl(product.image_url)" :alt="product.name" />
          </div>
          <p class="price">¥{{ product.price.toFixed(2) }}</p>
          <p class="desc">{{ product.description || '暂无描述' }}</p>
          <p class="stock">库存: {{ product.stock }}</p>
          <div class="action-buttons">
            <el-button
              size="small"
              :type="product.status ? 'warning' : 'success'"
              @click="toggleStatus(product)"
            >
              {{ product.status ? '下架' : '上架' }}
            </el-button>
            <el-button size="small" type="danger" @click="confirmDelete(product)">
              {{ product.status ? '删除' : '彻底删除' }}
            </el-button>
          </div>
        </div>
      </el-card>
      <el-empty v-if="products.length === 0" description="您还没有上架任何商品" />
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import http from '@/services/http'

const router = useRouter()
const store = useStore()
const currentUser = computed(() => store.getters['auth/currentUser']?.username || '')

const loading = ref(false)
const products = ref([])
const showAll = ref(false)

const toggleShowAll = () => {
  showAll.value = !showAll.value
  fetchMyProducts()
}

const fetchMyProducts = async () => {
  loading.value = true
  try {
    const res = await http.get('/api/ecommerce/products')
    const responseData = res.data || res
    const data = responseData.data || responseData

    if (responseData.code === 200) {
      const allProducts = Array.isArray(data) ? data : (data.items || [])
      let myProducts = allProducts.filter(p => p.seller_username === currentUser.value)

      if (!showAll.value) {
        myProducts = myProducts.filter(p => p.status === true)
      }

      products.value = myProducts
    } else {
      ElMessage.error(responseData.msg || '获取商品失败')
    }
  } catch (error) {
    console.error('加载商品失败:', error)
    ElMessage.error('网络错误，请检查后端服务是否启动')
  } finally {
    loading.value = false
  }
}

const getImageUrl = (imageUrl) => {
  if (!imageUrl) return ''
  if (imageUrl.startsWith('http')) return imageUrl
  const baseUrl = process.env.VUE_APP_API_BASE_URL || 'http://localhost:5000'
  return `${baseUrl}${imageUrl}`
}

const toggleStatus = async (product) => {
  try {
    const newStatus = !product.status
    const actionText = newStatus ? '上架' : '下架'

    await ElMessageBox.confirm(`确定要${actionText}这个商品吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const res = await http.put(`/api/ecommerce/products/${product.id}`, {
      status: newStatus
    })

    const responseData = res.data || res
    if (responseData.code === 200) {
      ElMessage.success(`商品已${actionText}`)
      fetchMyProducts()
    } else {
      ElMessage.error(responseData.msg || '操作失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('操作失败:', error)
      ElMessage.error('操作失败：' + (error.message || '未知错误'))
    }
  }
}

const confirmDelete = async (product) => {
  try {
    const message = product.status
      ? '删除商品将从列表中移除（变为下架状态），确定要删除吗？'
      : '此商品已下架，彻底删除将无法恢复，确定要继续吗？'

    await ElMessageBox.confirm(message, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    deleteProduct(product.id)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败：' + (error.message || '未知错误'))
    }
  }
}

const deleteProduct = async (productId) => {
  try {
    const res = await http.delete(`/api/ecommerce/products/${productId}`)
    const responseData = res.data || res

    if (responseData.code === 200) {
      ElMessage.success('操作成功')
      fetchMyProducts()
    } else {
      ElMessage.error(responseData.msg || '操作失败')
    }
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error('操作失败：' + (error.message || '未知错误'))
  }
}

const goToProductCenter = () => {
  router.push({ name: 'Products' })
}

onMounted(() => {
  fetchMyProducts()
})
</script>

<style scoped>
.my-products-page {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header h1 {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 600;
}

.page-header p {
  margin: 0;
  color: #666;
}

.action-bar {
  margin-top: 20px;
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
}

.loading-container {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.product-card {
  border-radius: 12px;
  transition: transform 0.2s;
}

.product-card:hover {
  transform: translateY(-5px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.product-name {
  font-weight: bold;
  font-size: 16px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.product-body {
  padding: 10px 0;
}

.product-image {
  width: 100%;
  height: 180px;
  margin-bottom: 12px;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f5f5;
}

.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.price {
  font-size: 20px;
  color: #ff6b6b;
  font-weight: bold;
  margin: 0 0 8px 0;
}

.desc {
  color: #666;
  font-size: 14px;
  margin-bottom: 8px;
  height: 40px;
  overflow: hidden;
}

.stock {
  color: #999;
  font-size: 12px;
  margin-bottom: 12px;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.action-buttons .el-button {
  flex: 1;
}
</style>
