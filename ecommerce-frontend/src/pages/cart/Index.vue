<template>
  <div class="cart-container">
    <div class="page-header">
      <h2>购物车</h2>
      <span class="cart-count">共 {{ totalItems }} 件商品</span>
    </div>

    <div v-loading="loading" class="cart-content">
      <el-empty v-if="items.length === 0" description="购物车是空的">
        <el-button type="primary" @click="goShopping">去逛逛</el-button>
      </el-empty>

      <template v-else>
        <el-card class="cart-main">
          <div class="table-header">
            <el-checkbox
              :model-value="isAllSelected"
              @change="handleSelectAll"
            >
              全选
            </el-checkbox>
            <el-button
              type="danger"
              text
              :disabled="selectedCount === 0"
              @click="handleBatchDelete"
            >
              删除选中
            </el-button>
          </div>

          <el-table
            :data="items"
            stripe
          >
            <el-table-column width="55">
              <template #default="{ row }">
                <el-checkbox
                  :model-value="row.selected"
                  @change="handleItemSelect(row.id, $event)"
                />
              </template>
            </el-table-column>

            <el-table-column label="商品信息" min-width="280">
              <template #default="{ row }">
                <div class="product-cell" @click="goProductDetail(row.product_id)">
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
                  <div class="product-info">
                    <span class="product-name">{{ row.product?.name || '商品信息' }}</span>
                    <span class="product-category">{{ row.product?.category }}</span>
                  </div>
                </div>
              </template>
            </el-table-column>

            <el-table-column label="单价" width="140">
              <template #default="{ row }">
                ¥{{ formatPrice(row.product?.price || 0) }}
              </template>
            </el-table-column>

            <el-table-column label="数量" width="160">
              <template #default="{ row }">
                <el-input-number
                  :model-value="row.quantity"
                  :min="1"
                  :max="row.product?.stock || 99"
                  size="small"
                  @update:model-value="handleQuantityChange(row.id, $event)"
                />
              </template>
            </el-table-column>

            <el-table-column label="小计" width="120">
              <template #default="{ row }">
                <span class="subtotal">¥{{ formatPrice((row.product?.price || 0) * row.quantity) }}</span>
              </template>
            </el-table-column>

            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <el-button
                  type="danger"
                  text
                  size="small"
                  @click="handleDelete(row.id)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card class="cart-footer">
          <div class="footer-content">
            <div class="footer-left">
              <el-button @click="goShopping">继续购物</el-button>
              <el-button @click="handleClearCart">清空购物车</el-button>
            </div>

            <div class="footer-right">
              <div class="summary">
                <span class="summary-item">
                  已选 <strong>{{ selectedCount }}</strong> 件商品
                </span>
                <span class="summary-item total-price">
                  合计: <strong>¥{{ formatPrice(totalAmount) }}</strong>
                </span>
              </div>
              <el-button
                type="primary"
                size="large"
                :disabled="selectedCount === 0"
                @click="showCheckoutDialog"
              >
                去结算
              </el-button>
            </div>
          </div>
        </el-card>

        <!-- 结算对话框 -->
        <el-dialog v-model="checkoutDialogVisible" title="确认订单" width="500px">
          <el-form ref="checkoutFormRef" :model="checkoutForm" :rules="checkoutRules" label-width="100px">
            <el-form-item label="收货地址" prop="shipping_address">
              <el-input
                v-model="checkoutForm.shipping_address"
                type="textarea"
                :rows="2"
                placeholder="请输入详细收货地址"
              />
            </el-form-item>
            <el-form-item label="联系电话" prop="contact_phone">
              <el-input v-model="checkoutForm.contact_phone" placeholder="请输入联系电话" />
            </el-form-item>
            <el-form-item label="订单备注">
              <el-input
                v-model="checkoutForm.remark"
                type="textarea"
                :rows="2"
                placeholder="可选：备注信息"
              />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="checkoutDialogVisible = false">取消</el-button>
            <el-button type="primary" :loading="checkoutLoading" @click="handleCheckout">
              确认下单
            </el-button>
          </template>
        </el-dialog>
      </template>
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

const loading = computed(() => store.getters['cart/isLoading']);
const items = computed(() => store.getters['cart/cartItems']);
const totalAmount = computed(() => store.getters['cart/totalAmount']);
const selectedCount = computed(() => store.getters['cart/selectedCount']);
const totalItems = computed(() => store.getters['cart/cartItemCount']);
const isAllSelected = computed({
  get: () => store.getters['cart/isAllSelected'],
  set: () => {}
});

// 结算对话框相关
const checkoutDialogVisible = ref(false);
const checkoutLoading = ref(false);
const checkoutFormRef = ref(null);
const checkoutForm = ref({
  shipping_address: '',
  contact_phone: '',
  remark: ''
});
const checkoutRules = {
  shipping_address: [
    { required: true, message: '请输入收货地址', trigger: 'blur' }
  ],
  contact_phone: [
    { required: true, message: '请输入联系电话', trigger: 'blur' }
  ]
};

function formatPrice(price) {
  return (price / 100).toFixed(2);
}

function goShopping() {
  router.push({ name: 'ProductList' });
}

function goProductDetail(productId) {
  router.push({ name: 'ProductDetail', params: { id: productId } });
}

function handleSelectAll(selected) {
  store.dispatch('cart/toggleAllSelect');
}

async function handleItemSelect(cartId, selected) {
  try {
    await store.dispatch('cart/toggleSelect', { cartId, selected });
  } catch (error) {
    ElMessage.error('更新失败');
  }
}

async function handleQuantityChange(cartId, quantity) {
  try {
    await store.dispatch('cart/updateQuantity', { cartId, quantity });
  } catch (error) {
    ElMessage.error('更新数量失败');
  }
}

async function handleDelete(cartId) {
  try {
    await ElMessageBox.confirm('确定要删除该商品吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    await store.dispatch('cart/removeItem', cartId);
    ElMessage.success('已删除');
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败');
    }
  }
}

async function handleBatchDelete() {
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedCount.value} 件商品吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    const selectedItems = store.getters['cart/selectedItems'];
    const ids = selectedItems.map(item => item.id);
    await store.dispatch('cart/batchRemove', ids);
    ElMessage.success('已删除');
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败');
    }
  }
}

async function handleClearCart() {
  try {
    await ElMessageBox.confirm('确定要清空购物车吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    await store.dispatch('cart/clearCart');
    ElMessage.success('购物车已清空');
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('清空失败');
    }
  }
}

function showCheckoutDialog() {
  checkoutDialogVisible.value = true;
}

async function handleCheckout() {
  const formEl = checkoutFormRef.value;
  if (!formEl) {
    ElMessage.error('表单初始化失败，请刷新重试');
    return;
  }

  try {
    await formEl.validate();
  } catch {
    return;
  }

  const selectedItems = store.getters['cart/selectedItems'];
  if (selectedItems.length === 0) {
    ElMessage.warning('请选择要结算的商品');
    return;
  }

  checkoutLoading.value = true;
  try {
    await store.dispatch('order/createOrder', {
      cartItemIds: selectedItems.map(item => item.id),
      shipping_address: checkoutForm.value.shipping_address.trim(),
      contact_phone: checkoutForm.value.contact_phone.trim(),
      remark: checkoutForm.value.remark?.trim() || ''
    });

    ElMessage.success('订单创建成功');
    checkoutDialogVisible.value = false;
    checkoutForm.value = { shipping_address: '', contact_phone: '', remark: '' };
    router.push({ name: 'OrderList' });
  } catch (error) {
    ElMessage.error(error.message || '结算失败，请重试');
  } finally {
    checkoutLoading.value = false;
  }
}

onMounted(async () => {
  await store.dispatch('cart/fetchCart');
});
</script>

<style scoped>
.cart-container {
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
  font-size: 20px;
  color: #303133;
}

.cart-count {
  color: #909399;
  font-size: 14px;
}

.cart-content {
  min-height: 400px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.product-cell {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.product-thumb {
  width: 60px;
  height: 60px;
  border-radius: 4px;
  flex-shrink: 0;
}

.thumb-placeholder {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  border-radius: 4px;
  color: #909399;
}

.product-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow: hidden;
}

.product-name {
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-category {
  font-size: 12px;
  color: #909399;
}

.subtotal {
  font-weight: 600;
  color: #f56c6c;
}

.cart-footer {
  margin-top: 16px;
}

.footer-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer-left {
  display: flex;
  gap: 12px;
}

.footer-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.summary {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.summary-item {
  font-size: 14px;
  color: #606266;
}

.summary-item strong {
  color: #409eff;
}

.total-price {
  font-size: 18px;
}

.total-price strong {
  color: #f56c6c;
  font-size: 22px;
}

@media (max-width: 768px) {
  .footer-content {
    flex-direction: column;
    gap: 16px;
  }

  .footer-right {
    flex-direction: column;
    width: 100%;
  }

  .summary {
    width: 100%;
    flex-direction: row;
    justify-content: space-between;
  }

  .footer-right .el-button {
    width: 100%;
  }
}
</style>
