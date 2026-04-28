<template>
  <div class="order-list-container">
    <div class="page-header">
      <h2>我的订单</h2>
    </div>

    <div class="status-tabs">
      <el-radio-group v-model="statusFilter" @change="handleStatusChange">
        <el-radio-button label="">全部</el-radio-button>
        <el-radio-button label="pending">待支付</el-radio-button>
        <el-radio-button label="paid">已支付</el-radio-button>
        <el-radio-button label="shipped">已发货</el-radio-button>
        <el-radio-button label="completed">已完成</el-radio-button>
        <el-radio-button label="cancelled">已取消</el-radio-button>
      </el-radio-group>
    </div>

    <div v-loading="loading" class="order-content">
      <el-empty v-if="!loading && orders.length === 0" description="暂无订单" />

      <div v-else class="order-list">
        <el-card
          v-for="order in orders"
          :key="order.id"
          class="order-card"
          @click="goDetail(order.id)"
        >
          <div class="order-header">
            <div class="order-info">
              <span class="order-no">订单号: {{ order.order_no }}</span>
              <span class="order-time">{{ formatDate(order.created_at) }}</span>
            </div>
            <div class="order-status">
              <el-tag :type="getStatusType(order.status)">
                {{ order.status_text }}
              </el-tag>
            </div>
          </div>

          <div class="order-items">
            <div
              v-for="item in order.items.slice(0, 3)"
              :key="item.id"
              class="order-item"
            >
              <el-image
                :src="item.product?.image_url"
                fit="cover"
                class="item-thumb"
              >
                <template #error>
                  <div class="thumb-placeholder">
                    <el-icon><Picture /></el-icon>
                  </div>
                </template>
              </el-image>
              <div class="item-info">
                <span class="item-name">{{ item.product_name }}</span>
                <span class="item-price">¥{{ formatPrice(item.price) }} x {{ item.quantity }}</span>
              </div>
            </div>
            <div v-if="order.items.length > 3" class="more-items">
              还有 {{ order.items.length - 3 }} 件商品
            </div>
          </div>

          <div class="order-footer">
            <div class="order-total">
              <span class="total-label">共 {{ order.item_count }} 件商品，合计:</span>
              <span class="total-amount">¥{{ formatPrice(order.total_amount) }}</span>
            </div>
            <div class="order-actions" @click.stop>
              <el-button
                v-if="order.status === 'pending'"
                type="danger"
                plain
                size="small"
                @click="handleCancel(order)"
              >
                取消订单
              </el-button>
              <el-button
                v-if="order.status === 'pending'"
                type="primary"
                size="small"
                @click="handlePay(order)"
              >
                去支付
              </el-button>
              <el-button
                v-if="order.status === 'shipped'"
                type="success"
                size="small"
                @click="handleConfirm(order)"
              >
                确认收货
              </el-button>
              <el-button
                v-if="['paid', 'shipped', 'completed'].includes(order.status)"
                type="info"
                plain
                size="small"
                @click="goDetail(order.id)"
              >
                查看详情
              </el-button>
            </div>
          </div>
        </el-card>
      </div>

      <div v-if="orders.length > 0" class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pagination.per_page"
          :total="pagination.total"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useStore } from 'vuex';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Picture } from '@element-plus/icons-vue';

const router = useRouter();
const store = useStore();

const statusFilter = ref('');
const currentPage = ref(1);

const orders = computed(() => store.getters['order/allOrders']);
const pagination = computed(() => store.getters['order/orderPagination']);
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

function goDetail(orderId) {
  router.push({ name: 'OrderDetail', params: { id: orderId } });
}

function handleStatusChange(status) {
  store.dispatch('order/setStatusFilter', status);
}

function handlePageChange(page) {
  store.dispatch('order/setPage', page);
}

async function handleCancel(order) {
  try {
    await ElMessageBox.confirm('确定要取消该订单吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    await store.dispatch('order/cancelOrder', order.id);
    ElMessage.success('订单已取消');
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('取消失败');
    }
  }
}

async function handlePay(order) {
  try {
    await store.dispatch('order/payOrder', {
      id: order.id,
      paymentMethod: 'alipay'
    });
    ElMessage.success('支付成功');
  } catch (error) {
    ElMessage.error('支付失败');
  }
}

async function handleConfirm(order) {
  try {
    await store.dispatch('order/confirmReceipt', order.id);
    ElMessage.success('确认收货成功');
  } catch (error) {
    ElMessage.error('确认收货失败');
  }
}

onMounted(() => {
  store.dispatch('order/fetchOrders');
});
</script>

<style scoped>
.order-list-container {
  max-width: 1000px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.status-tabs {
  margin-bottom: 20px;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
}

.order-content {
  min-height: 400px;
}

.order-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.order-card {
  cursor: pointer;
  transition: box-shadow 0.2s;
}

.order-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.order-info {
  display: flex;
  gap: 16px;
}

.order-no {
  font-weight: 600;
  color: #303133;
}

.order-time {
  color: #909399;
  font-size: 13px;
}

.order-items {
  display: flex;
  gap: 16px;
  padding: 16px 0;
  overflow-x: auto;
}

.order-item {
  display: flex;
  gap: 12px;
  min-width: 200px;
}

.item-thumb {
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

.item-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow: hidden;
}

.item-name {
  font-size: 13px;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 140px;
}

.item-price {
  font-size: 12px;
  color: #909399;
}

.more-items {
  display: flex;
  align-items: center;
  color: #909399;
  font-size: 13px;
  padding: 0 8px;
}

.order-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.order-total {
  display: flex;
  align-items: center;
  gap: 8px;
}

.total-label {
  color: #606266;
  font-size: 13px;
}

.total-amount {
  font-size: 18px;
  font-weight: 600;
  color: #f56c6c;
}

.order-actions {
  display: flex;
  gap: 8px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style>
