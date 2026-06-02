<template>
  <div class="orders-page">
    <div class="page-header">
      <h2>📦 我的订单</h2>
      <el-button type="primary" @click="loadOrders">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- 空状态 -->
    <el-empty v-else-if="orders.length === 0" description="暂无订单" />

    <!-- 订单列表 -->
    <div v-else class="order-list">
      <el-card v-for="order in orders" :key="order.id" class="order-card" shadow="hover">
        <template #header>
          <div class="order-header">
            <div>
              <span class="order-no">订单号：{{ order.order_no }}</span>
              <el-tag :type="getStatusType(order.status)" size="small">
                {{ getStatusText(order.status) }}
              </el-tag>
              <el-tag :type="getPaymentStatusType(order.payment_status)" size="small" style="margin-left: 8px;">
                {{ getPaymentStatusText(order.payment_status) }}
              </el-tag>
            </div>
            <span class="order-time">{{ formatTime(order.created_at) }}</span>
          </div>
        </template>

        <!-- 订单商品 -->
        <div class="order-items">
          <div v-for="item in order.items" :key="item.id" class="order-item">
            <div class="item-info">
              <h4>{{ item.product_name }}</h4>
              <p class="item-meta">
                单价：¥{{ item.product_price.toFixed(2) }} × {{ item.quantity }}
              </p>
            </div>
            <div class="item-subtotal">
              ¥{{ item.subtotal.toFixed(2) }}
            </div>
          </div>
        </div>

        <!-- 订单底部 -->
        <div class="order-footer">
          <div class="order-total">
            <span>订单总额：</span>
            <span class="total-amount">¥{{ order.total_amount.toFixed(2) }}</span>
          </div>
          <div class="order-actions">
            <el-button size="small" @click="viewDetail(order.id)">
              查看详情
            </el-button>
            <el-button
              v-if="canPay(order)"
              type="primary"
              size="small"
              @click="goToPayment(order.id)"
            >
              💳 去支付
            </el-button>
            <el-button
              v-if="canCancel(order)"
              type="danger"
              size="small"
              @click="handleCancel(order.id)"
            >
              取消订单
            </el-button>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 分页 -->
    <div v-if="pagination.total > pagination.per_page" class="pagination-container">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.per_page"
        :total="pagination.total"
        layout="total, prev, pager, next"
        @current-change="loadOrders"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import orderAPI from '@/services/api/orderAPI'

const router = useRouter()
const loading = ref(false)
const orders = ref([])
const pagination = ref({
  page: 1,
  per_page: 10,
  total: 0
})

// 加载订单列表
// 加载订单列表
const loadOrders = async () => {
  loading.value = true
  try {
    const response = await orderAPI.getUserOrders({
      page: pagination.value.page,
      per_page: pagination.value.per_page
    })

    // 修复：http.js 返回的是 axios response 对象，需要从 response.data 获取
    const responseData = response.data || response

    if (responseData.code === 200) {
      orders.value = responseData.data.items || []
      pagination.value.total = responseData.data.total || 0
    } else {
      ElMessage.error(responseData.msg || '加载订单失败')
    }
  } catch (error) {
    console.error('加载订单失败:', error)
    ElMessage.error('网络错误，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 查看详情
const viewDetail = (orderId) => {
  router.push({ name: 'OrderDetail', params: { orderId } })
}

// 去支付
const goToPayment = async (orderId) => {
  try {
    const response = await orderAPI.createPayment(orderId)

    // 修复：http.js 返回的是 axios response 对象
    const responseData = response.data || response

    if (responseData.code === 200) {
      const paymentUrl = responseData.data.payment_url

      // 保存当前页面路径，支付完成后返回
      sessionStorage.setItem('payment_return_url', window.location.href)

      // 浏览器跳转到银行支付页面
      window.location.href = paymentUrl
    } else {
      ElMessage.error(responseData.msg || '创建支付失败')
    }
  } catch (error) {
    console.error('创建支付失败:', error)
    ElMessage.error(error.response?.data?.msg || '创建支付失败')
  }
}




// 取消订单
const handleCancel = async (orderId) => {
  try {
    await ElMessageBox.confirm('确定要取消此订单吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const response = await orderAPI.cancelOrder(orderId)

    // 修复：http.js 返回的是 axios response 对象
    const responseData = response.data || response

    if (responseData.code === 200) {
      ElMessage.success('订单已取消')
      loadOrders() // 刷新列表
    } else {
      ElMessage.error(responseData.msg || '取消订单失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('取消订单失败:', error)
      ElMessage.error('取消订单失败')
    }
  }
}


// 判断是否可以支付
const canPay = (order) => {
  return order.status === 'pending' && order.payment_status === 'unpaid'
}

// 判断是否可以取消
const canCancel = (order) => {
  return order.status === 'pending'
}

// 获取订单状态类型
const getStatusType = (status) => {
  const types = {
    pending: 'warning',
    paid: 'success',
    shipped: 'primary',
    completed: 'success',
    cancelled: 'info'
  }
  return types[status] || ''
}

// 获取订单状态文本
const getStatusText = (status) => {
  const texts = {
    pending: '待支付',
    paid: '已支付',
    shipped: '已发货',
    completed: '已完成',
    cancelled: '已取消'
  }
  return texts[status] || status
}

// 获取支付状态类型
const getPaymentStatusType = (status) => {
  const types = {
    unpaid: 'info',
    paying: 'warning',
    paid: 'success',
    failed: 'danger'
  }
  return types[status] || ''
}

// 获取支付状态文本
const getPaymentStatusText = (status) => {
  const texts = {
    unpaid: '未支付',
    paying: '支付中',
    paid: '已支付',
    failed: '支付失败'
  }
  return texts[status] || status
}

// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
// 【新增】检查支付返回状态
const checkPaymentStatus = () => {
  const params = new URLSearchParams(window.location.search)
  const status = params.get('status')
  const orderId = params.get('order_id')

  if (status === 'success') {
    ElMessage.success(`订单 ${orderId} 支付成功！`)
    // 刷新订单列表
    loadOrders()
    // 清理 URL 参数，防止刷新页面重复提示
    window.history.replaceState({}, '', window.location.pathname)
  } else if (status === 'failed') {
    ElMessage.error(`订单 ${orderId} 支付失败，请重试。`)
    window.history.replaceState({}, '', window.location.pathname)
  }
}

onMounted(() => {
  checkPaymentStatus()
  loadOrders()
})
</script>

<style scoped>
.orders-page {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.loading-container {
  padding: 40px;
  background: white;
  border-radius: 8px;
}

.order-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.order-card {
  border-radius: 12px;
  transition: all 0.3s;
}

.order-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.order-no {
  font-weight: bold;
  color: #333;
  margin-right: 12px;
}

.order-time {
  color: #999;
  font-size: 13px;
}

.order-items {
  margin-bottom: 16px;
}

.order-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.order-item:last-child {
  border-bottom: none;
}

.item-info h4 {
  margin: 0 0 4px 0;
  font-size: 14px;
  color: #333;
}

.item-meta {
  margin: 0;
  font-size: 12px;
  color: #999;
}

.item-subtotal {
  font-weight: bold;
  color: #ff6b6b;
  font-size: 16px;
}

.order-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 2px solid #f5f5f5;
}

.order-total {
  font-size: 14px;
  color: #666;
}

.total-amount {
  font-size: 20px;
  font-weight: bold;
  color: #ff6b6b;
  margin-left: 8px;
}

.order-actions {
  display: flex;
  gap: 8px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 24px;
  padding: 16px;
  background: white;
  border-radius: 8px;
}
</style>
