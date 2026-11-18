<template>
  <div class="payment-page">
    <div class="payment-container">
      <h2>💳 确认支付</h2>

      <div v-if="loading" class="loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        <p>正在跳转到银行...</p>
      </div>

      <div v-else-if="error" class="error">
        <el-alert :title="error" type="error" :closable="false" />
        <el-button type="primary" @click="goBack" style="margin-top: 20px;">
          返回
        </el-button>
      </div>

      <div v-else class="order-info">
        <div class="info-item">
          <span class="label">订单号：</span>
          <span class="value">{{ orderInfo.order_no }}</span>
        </div>
        <div class="info-item">
          <span class="label">商品名称：</span>
          <span class="value">{{ orderInfo.items?.[0]?.product_name || '多个商品' }}</span>
        </div>
        <div class="info-item">
          <span class="label">支付金额：</span>
          <span class="value amount">¥{{ orderInfo.total_amount.toFixed(2) }}</span>
        </div>

        <div class="security-tips">
          <el-icon><Lock /></el-icon>
          <span>本交易采用国密SM2/SM3/SM4加密保护</span>
        </div>

        <div class="button-group">
          <el-button @click="goBack">取消</el-button>
          <el-button type="primary" size="large" @click="confirmPayment">
            确认支付
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Loading, Lock } from '@element-plus/icons-vue'

export default {
  name: 'PaymentPage',
  components: { Loading, Lock },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const loading = ref(false)
    const error = ref('')
    const orderInfo = ref({})
    const paymentUrl = ref('')

    const loadOrderInfo = async () => {
      const orderId = route.params.orderId
      if (!orderId) {
        error.value = '订单ID不能为空'
        return
      }

      loading.value = true
      try {
        const token = sessionStorage.getItem('auth.token')
        const response = await axios.get(`/api/ecommerce/orders/${orderId}`, {
          headers: { Authorization: `Bearer ${token}` }
        })

        if (response.data && response.data.success) {
          orderInfo.value = response.data.data

          // 创建支付请求
          await createPayment(orderId)
        } else {
          error.value = response.data?.message || '订单加载失败'
        }
      } catch (err) {
        error.value = '网络错误，请重试'
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    const createPayment = async (orderId) => {
      try {
        const token = sessionStorage.getItem('auth.token')
        const response = await axios.post(
          `/api/pay/create/${orderId}`,
          {},
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        )

        if (response.data && response.data.success) {
          paymentUrl.value = response.data.data.payment_url
        } else {
          error.value = response.data?.message || '创建支付失败'
        }
      } catch (err) {
        error.value = err.response?.data?.message || '创建支付失败'
        console.error(err)
      }
    }

    const confirmPayment = () => {
      if (!paymentUrl.value) {
        ElMessage.error('支付链接无效')
        return
      }

      // 浏览器跳转到银行支付页面
      window.location.href = paymentUrl.value
    }

    const goBack = () => {
      router.push('/profile')
    }

    onMounted(() => {
      loadOrderInfo()
    })

    return {
      loading,
      error,
      orderInfo,
      confirmPayment,
      goBack
    }
  }
}
</script>

<style scoped>
.payment-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.payment-container {
  background: white;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  padding: 40px;
  max-width: 500px;
  width: 90%;
}

h2 {
  text-align: center;
  color: #333;
  margin-bottom: 30px;
}

.loading {
  text-align: center;
  padding: 40px;
}

.loading .el-icon {
  font-size: 48px;
  color: #667eea;
  margin-bottom: 20px;
}

.error {
  padding: 20px;
}

.order-info {
  padding: 20px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 0;
  border-bottom: 1px solid #e0e0e0;
}

.info-item:last-of-type {
  border-bottom: none;
}

.label {
  color: #666;
  font-size: 14px;
}

.value {
  color: #333;
  font-weight: bold;
  font-size: 14px;
}

.amount {
  font-size: 24px;
  color: #ff6b6b;
}

.security-tips {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: 30px 0;
  padding: 15px;
  background: #f0f9ff;
  border-radius: 10px;
  color: #0ea5e9;
  font-size: 13px;
}

.button-group {
  display: flex;
  gap: 15px;
  margin-top: 30px;
}

.button-group .el-button {
  flex: 1;
}
</style>
