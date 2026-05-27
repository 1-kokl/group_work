<template>
  <div class="order-detail-page">
    <!-- 面包屑导航 -->
    <el-breadcrumb separator="/">
      <el-breadcrumb-item :to="{ name: 'Orders' }">我的订单</el-breadcrumb-item>
      <el-breadcrumb-item>订单详情</el-breadcrumb-item>
    </el-breadcrumb>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>

    <!-- 订单详情 -->
    <div v-else-if="order" class="detail-content">
      <!-- 订单状态卡片 -->
      <el-card class="status-card" shadow="hover">
        <div class="status-header">
          <div class="status-icon">
            <el-icon v-if="order.status === 'paid' || order.payment_status === 'paid'" :size="48" color="#67c23a">
              <CircleCheckFilled />
            </el-icon>
            <el-icon v-else-if="order.status === 'cancelled'" :size="48" color="#909399">
              <CircleCloseFilled />
            </el-icon>
            <el-icon v-else :size="48" color="#e6a23c">
              <Clock />
            </el-icon>
          </div>
          <div class="status-info">
            <h2>{{ getStatusText(order.status) }}</h2>
            <p class="order-no">订单号：{{ order.order_no }}</p>
            <p class="create-time">下单时间：{{ formatTime(order.created_at) }}</p>
          </div>
          <div class="action-buttons">
            <el-button
              v-if="canPay"
              type="primary"
              size="large"
              @click="handlePayment"
            >
              💳 立即支付
            </el-button>
            <el-button
              v-if="canCancel"
              type="danger"
              size="large"
              @click="handleCancel"
            >
              取消订单
            </el-button>
          </div>
        </div>
      </el-card>

      <!-- 订单信息 -->
      <el-row :gutter="20" style="margin-top: 20px;">
        <!-- 左侧：商品信息 -->
        <el-col :span="16">
          <el-card class="info-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span>📦 商品信息</span>
              </div>
            </template>
            <div class="product-list">
              <div v-for="item in order.items" :key="item.id" class="product-item">
                <div class="product-info">
                  <h4>{{ item.product_name }}</h4>
                  <p class="product-meta">
                    单价：¥{{ item.product_price.toFixed(2) }} × {{ item.quantity }}
                  </p>
                </div>
                <div class="product-price">
                  ¥{{ item.subtotal.toFixed(2) }}
                </div>
              </div>
            </div>
            <div class="order-summary">
              <div class="summary-row">
                <span>商品总额：</span>
                <span>¥{{ order.total_amount.toFixed(2) }}</span>
              </div>
              <div class="summary-row">
                <span>运费：</span>
                <span>¥0.00</span>
              </div>
              <div class="summary-row total">
                <span>应付总额：</span>
                <span class="amount">¥{{ order.total_amount.toFixed(2) }}</span>
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 右侧：订单信息 -->
        <el-col :span="8">
          <el-card class="info-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span>📋 订单信息</span>
              </div>
            </template>
            <div class="order-info-list">
              <div class="info-item">
                <span class="label">订单状态：</span>
                <el-tag :type="getStatusType(order.status)">
                  {{ getStatusText(order.status) }}
                </el-tag>
              </div>
              <div class="info-item">
                <span class="label">支付状态：</span>
                <el-tag :type="getPaymentStatusType(order.payment_status)">
                  {{ getPaymentStatusText(order.payment_status) }}
                </el-tag>
              </div>
              <div class="info-item">
                <span class="label">收货地址：</span>
                <span class="value">{{ order.shipping_address || '-' }}</span>
              </div>
              <div class="info-item">
                <span class="label">联系电话：</span>
                <span class="value">{{ order.contact_phone || '-' }}</span>
              </div>
              <div class="info-item" v-if="order.remark">
                <span class="label">订单备注：</span>
                <span class="value">{{ order.remark }}</span>
              </div>
              <div class="info-item">
                <span class="label">下单时间：</span>
                <span class="value">{{ formatTime(order.created_at) }}</span>
              </div>
              <div class="info-item" v-if="order.paid_at">
                <span class="label">支付时间：</span>
                <span class="value">{{ formatTime(order.paid_at) }}</span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 空状态 -->
    <el-empty v-else description="订单不存在" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { CircleCheckFilled, CircleCloseFilled, Clock } from '@element-plus/icons-vue'
import orderAPI from '@/services/api/orderAPI'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const order = ref(null)

// 是否可以支付
const canPay = computed(() => {
  return order.value && order.value.status === 'pending' && order.value.payment_status === 'unpaid'
})

// 是否可以取消
const canCancel = computed(() => {
  return order.value && order.value.status === 'pending'
})

// 加载订单详情
const loadOrderDetail = async () => {
  const orderId = route.params.orderId
  if (!orderId) {
    ElMessage.error('订单ID不能为空')
    router.push({ name: 'Orders' })
    return
  }

  loading.value = true
  try {
    const response = await orderAPI.getOrderDetail(orderId)

    if (response.code === 200) {
      order.value = response.data
    } else {
      ElMessage.error(response.msg || '加载订单失败')
    }
  } catch (error) {
    console.error('加载订单失败:', error)
    ElMessage.error('网络错误，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 去支付
const handlePayment = async () => {
  try {
    const response = await orderAPI.createPayment(order.value.id)

    if (response.code === 200) {
      const paymentUrl = response.data.payment_url
      // 浏览器跳转到银行支付页面
      window.location.href = paymentUrl
    } else {
      ElMessage.error(response.msg || '创建支付失败')
    }
  } catch (error) {
    console.error('创建支付失败:', error)
    ElMessage.error(error.response?.data?.msg || '创建支付失败')
  }
}

// 取消订单
const handleCancel = async () => {
  try {
    await ElMessageBox.confirm('确定要取消此订单吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const response = await orderAPI.cancelOrder(order.value.id)

    if (response.code === 200) {
      ElMessage.success('订单已取消')
      loadOrderDetail() // 刷新详情
    } else {
      ElMessage.error(response.msg || '取消订单失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('取消订单失败:', error)
      ElMessage.error('取消订单失败')
    }
  }
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
    minute: '2-digit',
    second: '2-digit'
  })
}

onMounted(() => {
  loadOrderDetail()
})
</script>

<style scoped>
.order-detail-page {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.loading-container {
  padding: 40px;
  background: white;
  border-radius: 8px;
}

.detail-content {
  margin-top: 20px;
}

.status-card {
  border-radius: 12px;
}

.status-header {
  display: flex;
  align-items: center;
  gap: 24px;
}

.status-icon {
  flex-shrink: 0;
}

.status-info {
  flex: 1;
}

.status-info h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #333;
}

.order-no {
  margin: 4px 0;
  color: #666;
  font-size: 14px;
}

.create-time {
  margin: 4px 0;
  color: #999;
  font-size: 13px;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.info-card {
  border-radius: 12px;
  height: 100%;
}

.card-header {
  font-weight: bold;
  font-size: 16px;
}

.product-list {
  margin-bottom: 20px;
}

.product-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
}

.product-item:last-child {
  border-bottom: none;
}

.product-info h4 {
  margin: 0 0 8px 0;
  font-size: 15px;
  color: #333;
}

.product-meta {
  margin: 0;
  font-size: 13px;
  color: #999;
}

.product-price {
  font-weight: bold;
  color: #ff6b6b;
  font-size: 18px;
}

.order-summary {
  padding-top: 20px;
  border-top: 2px solid #f5f5f5;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  font-size: 14px;
  color: #666;
}

.summary-row.total {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e0e0e0;
  font-size: 16px;
  font-weight: bold;
  color: #333;
}

.summary-row.total .amount {
  font-size: 24px;
  color: #ff6b6b;
}

.order-info-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-item .label {
  font-size: 13px;
  color: #999;
}

.info-item .value {
  font-size: 14px;
  color: #333;
}
</style>
