<template>
  <div class="order-detail-container">
    <el-button text @click="goBack">
      <el-icon><ArrowLeft /></el-icon>
      返回订单列表
    </el-button>

    <div v-loading="loading" class="detail-content">
      <el-empty v-if="!loading && !order" description="订单不存在" />

      <template v-else-if="order">
        <el-card class="order-info-card">
          <template #header>
            <div class="card-header">
              <span>订单信息</span>
              <el-tag :type="getStatusType(order.status)">
                {{ order.status_text }}
              </el-tag>
            </div>
          </template>

          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">订单编号</span>
              <span class="info-value">{{ order.order_no }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">下单时间</span>
              <span class="info-value">{{ formatDate(order.created_at) }}</span>
            </div>
            <div v-if="order.paid_at" class="info-item">
              <span class="info-label">支付时间</span>
              <span class="info-value">{{ formatDate(order.paid_at) }}</span>
            </div>
            <div v-if="order.shipped_at" class="info-item">
              <span class="info-label">发货时间</span>
              <span class="info-value">{{ formatDate(order.shipped_at) }}</span>
            </div>
            <div v-if="order.completed_at" class="info-item">
              <span class="info-label">完成时间</span>
              <span class="info-value">{{ formatDate(order.completed_at) }}</span>
            </div>
            <div v-if="order.cancelled_at" class="info-item">
              <span class="info-label">取消时间</span>
              <span class="info-value">{{ formatDate(order.cancelled_at) }}</span>
            </div>
          </div>

          <el-divider />

          <div class="status-timeline">
            <el-steps :active="getStepActive(order.status)" finish-status="success" align-center>
              <el-step title="下单" :description="formatDate(order.created_at)" />
              <el-step title="支付" :description="order.paid_at ? formatDate(order.paid_at) : '-'" />
              <el-step title="发货" :description="order.shipped_at ? formatDate(order.shipped_at) : '-'" />
              <el-step title="完成" :description="order.completed_at ? formatDate(order.completed_at) : '-'" />
            </el-steps>
          </div>
        </el-card>

        <el-card class="items-card">
          <template #header>
            <span>商品明细</span>
          </template>

          <el-table :data="order.items" stripe>
            <el-table-column label="商品" min-width="300">
              <template #default="{ row }">
                <div class="product-cell">
                  <el-image
                    :src="row.product?.image_url"
                    fit="cover"
                    class="product-thumb"
                  >
                    <template #error>
                      <div class="thumb-placeholder">
                        <el-icon><Picture /></el-icon>
                      </div>
                    </template>
                  </el-image>
                  <span class="product-name">{{ row.product_name }}</span>
                </div>
              </template>
            </el-table-column>

            <el-table-column label="单价" width="140">
              <template #default="{ row }">
                ¥{{ formatPrice(row.price) }}
              </template>
            </el-table-column>

            <el-table-column label="数量" width="100">
              <template #default="{ row }">
                x {{ row.quantity }}
              </template>
            </el-table-column>

            <el-table-column label="小计" width="140">
              <template #default="{ row }">
                <span class="subtotal">¥{{ formatPrice(row.subtotal) }}</span>
              </template>
            </el-table-column>
          </el-table>

          <div class="order-summary">
            <div class="summary-row">
              <span>商品总数</span>
              <span>{{ order.item_count }} 件</span>
            </div>
            <div class="summary-row total">
              <span>订单总额</span>
              <span class="total-amount">¥{{ formatPrice(order.total_amount) }}</span>
            </div>
          </div>
        </el-card>

        <el-card v-if="order.status === 'pending'" class="actions-card">
          <div class="action-buttons">
            <el-button type="danger" plain @click="handleCancel">取消订单</el-button>
            <el-button type="primary" @click="handlePay">去支付</el-button>
          </div>
        </el-card>

        <el-card v-if="order.status === 'shipped'" class="actions-card">
          <div class="action-buttons">
            <el-button type="success" @click="handleConfirm">确认收货</el-button>
          </div>
        </el-card>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useStore } from 'vuex';
import { ElMessage, ElMessageBox } from 'element-plus';
import { ArrowLeft, Picture } from '@element-plus/icons-vue';

const route = useRoute();
const router = useRouter();
const store = useStore();

const order = computed(() => store.getters['order/currentOrder']);
const loading = computed(() => store.getters['order/isLoading']);

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

function getStatusType(status) {
  const typeMap = {
    pending: 'warning',
    paid: 'success',
    shipped: 'primary',
    completed: 'info',
    cancelled: 'info'
  };
  return typeMap[status] || 'info';
}

function getStepActive(status) {
  const stepMap = {
    pending: 0,
    paid: 1,
    shipped: 2,
    completed: 3,
    cancelled: -1
  };
  return stepMap[status] ?? 0;
}

function goBack() {
  router.push({ name: 'OrderList' });
}

async function handleCancel() {
  try {
    await ElMessageBox.confirm('确定要取消该订单吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    await store.dispatch('order/cancelOrder', order.value.id);
    ElMessage.success('订单已取消');
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('取消失败');
    }
  }
}

async function handlePay() {
  try {
    await store.dispatch('order/payOrder', {
      id: order.value.id,
      paymentMethod: 'alipay'
    });
    ElMessage.success('支付成功');
  } catch (error) {
    ElMessage.error('支付失败');
  }
}

async function handleConfirm() {
  try {
    await store.dispatch('order/confirmReceipt', order.value.id);
    ElMessage.success('确认收货成功');
  } catch (error) {
    ElMessage.error('确认收货失败');
  }
}

onMounted(async () => {
  const orderId = route.params.id;
  await store.dispatch('order/fetchOrderDetail', orderId);
});
</script>

<style scoped>
.order-detail-container {
  max-width: 1000px;
  margin: 0 auto;
}

.detail-content {
  margin-top: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 13px;
  color: #909399;
}

.info-value {
  font-size: 14px;
  color: #303133;
}

.status-timeline {
  padding: 20px 0;
}

.items-card {
  margin-top: 16px;
}

.product-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.product-thumb {
  width: 50px;
  height: 50px;
  border-radius: 4px;
  flex-shrink: 0;
}

.thumb-placeholder {
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  border-radius: 4px;
  color: #909399;
}

.product-name {
  font-size: 14px;
  color: #303133;
}

.subtotal {
  font-weight: 600;
  color: #f56c6c;
}

.order-summary {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.summary-row {
  display: flex;
  gap: 24px;
  font-size: 14px;
  color: #606266;
}

.summary-row.total {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.total-amount {
  font-size: 20px;
  color: #f56c6c;
}

.actions-card {
  margin-top: 16px;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 16px;
}

@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
