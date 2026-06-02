<template>
  <section class="dashboard-page">
    <header class="dashboard-header">
      <h1>🛍️ 商品管理中心</h1>
      <p>在这里您可以浏览平台商品或上架自己的新产品。</p>
    </header>

    <!-- 操作栏 -->
    <div class="action-bar">
      <el-button type="primary" @click="showAddDialog = true">
        <el-icon><Plus /></el-icon> 添加新商品
      </el-button>
      <el-button @click="fetchProducts">
        <el-icon><Refresh /></el-icon> 刷新列表
      </el-button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="3" animated />
    </div>

    <!-- 商品列表 -->
    <div v-else class="product-grid">
      <el-card v-for="product in products" :key="product.id" class="product-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="product-name">{{ product.name }}</span>
            <el-tag v-if="product.seller_username === currentUser" type="success" size="small">我的商品</el-tag>
          </div>
        </template>
        <div class="product-body">
          <p class="price">¥{{ product.price.toFixed(2) }}</p>
          <p class="desc">{{ product.description || '暂无描述' }}</p>
          <p class="seller">卖家: {{ product.seller_username }}</p>
        </div>
      </el-card>
      <!-- 空状态 -->
      <el-empty v-if="products.length === 0" description="暂无商品，快去添加吧！" />
    </div>

    <!-- 添加商品对话框 -->
    <el-dialog v-model="showAddDialog" title="添加新商品" width="500px">
      <el-form :model="newProduct" label-width="80px">
        <el-form-item label="商品名称">
          <el-input v-model="newProduct.name" placeholder="请输入商品名称" />
        </el-form-item>
        <el-form-item label="价格">
          <el-input-number v-model="newProduct.price" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="newProduct.description" type="textarea" rows="3" placeholder="请输入商品描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddDialog = false">取消</el-button>
          <el-button type="primary" @click="submitProduct" :loading="submitting">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import http from '@/services/http'

// Store
const store = useStore()
const currentUser = computed(() => store.getters['auth/currentUser']?.username || '')

// 状态定义
const loading = ref(false)
const submitting = ref(false)
const showAddDialog = ref(false)
const products = ref([])

// 新商品表单
const newProduct = ref({
  name: '',
  price: 0,
  description: ''
})


// 获取商品列表
const fetchProducts = async () => {
  loading.value = true
  try {
    const res = await http.get('/api/ecommerce/products')

    const responseData = res.data || res
    const data = responseData.data || responseData

    if (responseData.code === 200) {
      products.value = Array.isArray(data) ? data : (data.items || [])
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

// 提交新商品
const submitProduct = async () => {
  if (!newProduct.value.name || newProduct.value.price <= 0) {
    ElMessage.warning('请填写完整的商品信息')
    return
  }

  submitting.value = true
  try {
    const res = await http.post('/api/ecommerce/products', newProduct.value)

    const responseData = res.data || res

    if (responseData.code === 200 || responseData.code === 201) {
      ElMessage.success('添加成功')
      showAddDialog.value = false
      newProduct.value = { name: '', price: 0, description: '' }
      fetchProducts()
    } else {
      ElMessage.error(responseData.msg || '添加失败')
    }
  } catch (error) {
    console.error('添加商品失败:', error)
    ElMessage.error('添加失败：' + (error.message || '未知错误'))
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchProducts()
})
</script>


<style scoped>
.dashboard-page {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.dashboard-header h1 {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 600;
}

.dashboard-header p {
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
  height: 40px; /* 限制高度 */
  overflow: hidden;
}

.seller {
  color: #999;
  font-size: 12px;
  margin: 0;
}
</style>
