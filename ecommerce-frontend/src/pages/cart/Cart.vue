<template>
  <section class="cart-page">
    <header class="page-header">
      <h1>🛒 我的购物车</h1>
      <p>选择商品进行结算</p>
    </header>

    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>

    <div v-else-if="cartItems.length === 0" class="empty-cart">
      <el-empty description="购物车是空的">
        <el-button type="primary" @click="goToProducts">去逛逛</el-button>
      </el-empty>
    </div>

    <div v-else class="cart-content">
      <div class="cart-items">
        <el-card v-for="item in cartItems" :key="item.id" class="cart-item-card" shadow="hover">
          <div class="cart-item-content">
            <div class="item-checkbox">
              <el-checkbox v-model="item.selected" @change="updateSelection(item)" />
            </div>

            <div class="item-image">
              <img v-if="item.product_image" :src="getImageUrl(item.product_image)" :alt="item.product_name" />
              <el-icon v-else class="no-image"><Picture /></el-icon>
            </div>

            <div class="item-info">
              <h3 class="item-name">{{ item.product_name }}</h3>
              <p class="item-price">¥{{ item.product_price.toFixed(2) }}</p>
              <p class="item-id">商品ID: {{ item.product_id.slice(0, 8) }}...</p>
            </div>

            <div class="item-quantity">
              <el-input-number
                v-model="item.quantity"
                :min="1"
                :max="99"
                @change="updateQuantity(item)"
              />
            </div>

            <div class="item-subtotal">
              <span class="subtotal-label">小计：</span>
              <span class="subtotal-value">¥{{ (item.product_price * item.quantity).toFixed(2) }}</span>
            </div>

            <div class="item-actions">
              <el-button type="danger" text @click="removeItem(item.id)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </div>
        </el-card>
      </div>

      <div class="cart-summary">
        <el-card class="summary-card">
          <div class="summary-header">
            <h3>订单摘要</h3>
          </div>

          <div class="summary-row">
            <span>已选商品：</span>
            <span>{{ selectedCount }} 件</span>
          </div>

          <div class="summary-row total">
            <span>合计：</span>
            <span class="total-price">¥{{ totalPrice.toFixed(2) }}</span>
          </div>

          <div class="summary-actions">
            <el-button @click="clearCart" :disabled="cartItems.length === 0">
              清空购物车
            </el-button>
            <el-button
              type="primary"
              size="large"
              :disabled="selectedCount === 0"
              @click="checkout"
            >
              结算 ({{ selectedCount }})
            </el-button>
          </div>
        </el-card>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Picture, Delete } from '@element-plus/icons-vue'
import http from '@/services/http'

const router = useRouter()
const loading = ref(false)
const cartItems = ref([])

const selectedCount = computed(() => {
  return cartItems.value.filter(item => item.selected).reduce((sum, item) => sum + item.quantity, 0)
})

const totalPrice = computed(() => {
  return cartItems.value
    .filter(item => item.selected)
    .reduce((sum, item) => sum + item.product_price * item.quantity, 0)
})

const fetchCart = async () => {
  loading.value = true
  try {
    const res = await http.get('/api/ecommerce/cart')
    const responseData = res.data || res

    if (responseData.code === 200) {
      cartItems.value = (responseData.data || []).map(item => ({
        ...item,
        selected: item.selected !== false
      }))
    } else {
      ElMessage.error(responseData.msg || '获取购物车失败')
    }
  } catch (error) {
    console.error('加载购物车失败:', error)
    ElMessage.error('网络错误，请检查后端服务')
  } finally {
    loading.value = false
  }
}

const updateSelection = async (item) => {
  try {
    const res = await http.put(`/api/ecommerce/cart/${item.id}`, {
      selected: item.selected
    })

    const responseData = res.data || res
    if (responseData.code !== 200) {
      ElMessage.error('更新失败')
      item.selected = !item.selected
    }
  } catch (error) {
    console.error('更新选中状态失败:', error)
    item.selected = !item.selected
  }
}

const updateQuantity = async (item) => {
  try {
    const res = await http.put(`/api/ecommerce/cart/${item.id}`, {
      quantity: item.quantity
    })

    const responseData = res.data || res
    if (responseData.code !== 200) {
      ElMessage.error('更新数量失败')
    }
  } catch (error) {
    console.error('更新数量失败:', error)
    ElMessage.error('更新失败')
  }
}

const removeItem = async (cartId) => {
  try {
    await ElMessageBox.confirm('确定要移除这个商品吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const res = await http.delete(`/api/ecommerce/cart/${cartId}`)
    const responseData = res.data || res

    if (responseData.code === 200) {
      ElMessage.success('已移除')
      fetchCart()
    } else {
      ElMessage.error(responseData.msg || '移除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('移除失败:', error)
      ElMessage.error('移除失败')
    }
  }
}

const clearCart = async () => {
  try {
    await ElMessageBox.confirm('确定要清空购物车吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const res = await http.delete('/api/ecommerce/cart/clear')
    const responseData = res.data || res

    if (responseData.code === 200) {
      ElMessage.success('购物车已清空')
      fetchCart()
    } else {
      ElMessage.error(responseData.msg || '清空失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清空失败:', error)
      ElMessage.error('清空失败')
    }
  }
}

const checkout = async () => {
  const selectedItems = cartItems.value.filter(item => item.selected)

  if (selectedItems.length === 0) {
    ElMessage.warning('请选择要结算的商品')
    return
  }

  try {
    const res = await http.post('/api/ecommerce/orders', {
      shipping_address: '测试地址',
      contact_phone: '13800138000',
      cart_item_ids: selectedItems.map(item => item.id)
    })

    const responseData = res.data || res

    if (responseData.code === 201 || responseData.code === 200) {
      ElMessage.success('订单创建成功')
      router.push({ name: 'Orders' })
    } else {
      ElMessage.error(responseData.msg || '下单失败')
    }
  } catch (error) {
    console.error('下单失败:', error)
    ElMessage.error('下单失败：' + (error.message || '未知错误'))
  }
}

const getImageUrl = (imageUrl) => {
  if (!imageUrl) return ''
  if (imageUrl.startsWith('http')) return imageUrl
  const baseUrl = process.env.VUE_APP_API_BASE_URL || 'http://localhost:5000'
  return `${baseUrl}${imageUrl}`
}

const goToProducts = () => {
  router.push({ name: 'Products' })
}

onMounted(() => {
  fetchCart()
})
</script>

<style scoped>
.cart-page {
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

.loading-container {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
}

.empty-cart {
  padding: 60px 0;
  text-align: center;
}

.cart-content {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 24px;
  margin-top: 24px;
}

.cart-items {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.cart-item-card {
  border-radius: 8px;
}

.cart-item-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.item-checkbox {
  flex-shrink: 0;
}

.item-image {
  width: 100px;
  height: 100px;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.item-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.no-image {
  font-size: 32px;
  color: #ccc;
}

.item-info {
  flex: 1;
  min-width: 0;
}

.item-name {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-price {
  margin: 4px 0;
  color: #f56c6c;
  font-weight: 600;
  font-size: 18px;
}

.item-id {
  margin: 4px 0;
  color: #999;
  font-size: 12px;
  font-family: monospace;
}

.item-quantity {
  flex-shrink: 0;
}

.item-subtotal {
  flex-shrink: 0;
  text-align: right;
  min-width: 120px;
}

.subtotal-label {
  color: #606266;
  font-size: 14px;
}

.subtotal-value {
  color: #f56c6c;
  font-size: 20px;
  font-weight: 600;
}

.item-actions {
  flex-shrink: 0;
}

.summary-card {
  border-radius: 8px;
  position: sticky;
  top: 24px;
}

.summary-header h3 {
  margin: 0 0 16px;
  font-size: 18px;
  color: #303133;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #ebeef5;
  color: #606266;
}

.summary-row.total {
  border-bottom: none;
  padding: 16px 0;
  font-size: 16px;
  font-weight: 600;
}

.total-price {
  color: #f56c6c;
  font-size: 24px;
}

.summary-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 20px;
}

.summary-actions .el-button {
  width: 100%;
}

@media (max-width: 768px) {
  .cart-content {
    grid-template-columns: 1fr;
  }

  .cart-item-content {
    flex-wrap: wrap;
  }

  .item-info {
    width: 100%;
  }
}
</style>
