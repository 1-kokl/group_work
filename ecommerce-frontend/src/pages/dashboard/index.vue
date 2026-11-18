<template>
  <section class="dashboard-page">
    <header class="dashboard-header">
      <h1>🛍️ 商品管理中心</h1>
      <p>在这里您可以浏览平台商品或上架自己的新产品。</p>
    </header>

    <div class="action-bar">
      <el-button type="primary" @click="showAddDialog = true">
        <el-icon><Plus /></el-icon> 添加新商品
      </el-button>
      <el-button @click="fetchProducts">
        <el-icon><Refresh /></el-icon> 刷新列表
      </el-button>
    </div>

    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="3" animated />
    </div>

    <div v-else class="product-grid">
      <el-card
        v-for="product in products"
        :key="product.id"
        class="product-card"
        shadow="hover"
        @click="viewProduct(product.id)"
        style="cursor: pointer;"
      >
        <template #header>
          <div class="card-header">
            <span class="product-name">{{ product.name }}</span>
            <el-tag v-if="product.seller_username === currentUser" type="success" size="small">我的商品</el-tag>
          </div>
        </template>
        <div class="product-body">
          <div v-if="product.image_url" class="product-image">
            <img :src="getImageUrl(product.image_url)" :alt="product.name" />
          </div>
          <p class="price">¥{{ product.price.toFixed(2) }}</p>
          <p class="desc">{{ product.description || '暂无描述' }}</p>
          <p class="seller">卖家: {{ product.seller_username || '未知' }}</p>
          <p class="product-id">商品ID: {{ product.id.slice(0, 8) }}...</p>
        </div>
      </el-card>
      <el-empty v-if="products.length === 0" description="暂无商品，快去添加吧！" />
    </div>

    <el-dialog v-model="showAddDialog" title="添加新商品" width="500px">
      <el-form :model="newProduct" label-width="80px">
        <el-form-item label="商品名称">
          <el-input v-model="newProduct.name" placeholder="请输入商品名称" />
        </el-form-item>
        <el-form-item label="价格">
          <el-input-number v-model="newProduct.price" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="库存">
          <el-input-number v-model="newProduct.stock" :min="1" :step="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="newProduct.description" type="textarea" rows="3" placeholder="请输入商品描述" />
        </el-form-item>
        <el-form-item label="商品图片">
          <el-upload
            class="image-uploader"
            action="#"
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handleImageChange"
            accept="image/*"
          >
            <img v-if="imagePreview" :src="imagePreview" class="uploaded-image" />
            <el-icon v-else class="uploader-icon"><Plus /></el-icon>
          </el-upload>
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
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import http from '@/services/http'

const router = useRouter()
const store = useStore()
const currentUser = computed(() => store.getters['auth/currentUser']?.username || '')

const loading = ref(false)
const submitting = ref(false)
const showAddDialog = ref(false)
const products = ref([])
const imageFile = ref(null)
const imagePreview = ref(null)

const newProduct = ref({
  name: '',
  price: 0,
  stock: 1,
  description: ''
})

const fetchProducts = async () => {
  loading.value = true
  try {
    const res = await http.get('/api/ecommerce/products')

    const responseData = res.data || res
    const data = responseData.data || responseData

    if (responseData.code === 200) {
      const allProducts = Array.isArray(data) ? data : (data.items || [])
      products.value = allProducts.filter(p => p.status === true)
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

const handleImageChange = (file) => {
  imageFile.value = file.raw
  imagePreview.value = URL.createObjectURL(file.raw)
}

const uploadImage = async () => {
  if (!imageFile.value) return null

  const formData = new FormData()
  formData.append('image', imageFile.value)

  try {
    const res = await http.post('/api/ecommerce/upload-image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    const responseData = res.data || res
    if (responseData.code === 200) {
      return responseData.data.image_url
    }
    return null
  } catch (error) {
    console.error('图片上传失败:', error)
    return null
  }
}

const submitProduct = async () => {
  if (!newProduct.value.name || newProduct.value.price <= 0) {
    ElMessage.warning('请填写完整的商品信息')
    return
  }

  submitting.value = true
  try {
    let imageUrl = null
    if (imageFile.value) {
      imageUrl = await uploadImage()
    }

    const productData = {
      name: newProduct.value.name,
      price: newProduct.value.price,
      stock: newProduct.value.stock,
      description: newProduct.value.description,
      image_url: imageUrl
    }

    const res = await http.post('/api/ecommerce/products', productData)

    const responseData = res.data || res

    if (responseData.code === 200 || responseData.code === 201) {
      ElMessage.success('添加成功')
      showAddDialog.value = false
      newProduct.value = { name: '', price: 0, stock: 1, description: '' }
      imageFile.value = null
      imagePreview.value = null
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

const viewProduct = (productId) => {
  router.push({ name: 'ProductDetail', params: { id: productId } })
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

.seller {
  color: #999;
  font-size: 12px;
  margin: 0;
}

.product-id {
  color: #bbb;
  font-size: 11px;
  margin: 4px 0 0;
  font-family: monospace;
}

.image-uploader {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  width: 148px;
  height: 148px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-uploader:hover {
  border-color: #409eff;
}

.uploaded-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.uploader-icon {
  font-size: 28px;
  color: #8c939d;
}
</style>
