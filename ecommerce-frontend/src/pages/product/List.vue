<template>
  <div class="product-list-container">
    <div class="page-header">
      <h2>商品列表</h2>
      <el-button type="primary" @click="goCreate">
        <el-icon><Plus /></el-icon>
        发布商品
      </el-button>
    </div>

    <div class="filter-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索商品名称或描述"
        clearable
        style="width: 240px"
        @clear="handleSearch"
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <el-select
        v-model="filterCategory"
        placeholder="选择分类"
        clearable
        style="width: 160px"
        @change="handleSearch"
      >
        <el-option
          v-for="cat in categories"
          :key="cat.id"
          :label="cat.name"
          :value="cat.name"
        />
      </el-select>

      <el-select
        v-model="filterSort"
        style="width: 140px"
        @change="handleSearch"
      >
        <el-option label="最新上架" value="created_desc" />
        <el-option label="价格从低到高" value="price_asc" />
        <el-option label="价格从高到低" value="price_desc" />
      </el-select>

      <el-button @click="resetFilters">重置</el-button>
    </div>

    <div v-loading="loading" class="product-grid">
      <el-empty v-if="!loading && products.length === 0" description="暂无商品" />

      <div v-else class="grid-container">
        <el-card
          v-for="product in products"
          :key="product.id"
          class="product-card"
          :body-style="{ padding: '0px' }"
          shadow="hover"
          @click="goDetail(product.id)"
        >
          <div class="product-image">
            <el-image
              :src="product.image_url"
              fit="cover"
              class="image"
            >
              <template #error>
                <div class="image-slot">
                  <el-icon><Picture /></el-icon>
                </div>
              </template>
            </el-image>
            <el-tag class="category-tag" type="info">{{ product.category }}</el-tag>
          </div>

          <div class="product-info">
            <h3 class="product-name">{{ product.name }}</h3>
            <p class="product-desc">{{ product.description }}</p>
            <div class="product-footer">
              <span class="product-price">¥{{ formatPrice(product.price) }}</span>
              <span class="product-stock">库存: {{ product.stock }}</span>
            </div>
            <el-button
              type="primary"
              size="small"
              class="add-cart-btn"
              @click.stop="handleAddToCart(product)"
            >
              加入购物车
            </el-button>
          </div>
        </el-card>
      </div>
    </div>

    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pagination.per_page"
        :total="pagination.total"
        layout="total, prev, pager, next"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useStore } from 'vuex';
import { ElMessage } from 'element-plus';
import { Plus, Search, Picture } from '@element-plus/icons-vue';

const router = useRouter();
const store = useStore();

const searchKeyword = ref('');
const filterCategory = ref('');
const filterSort = ref('created_desc');
const currentPage = ref(1);

const products = computed(() => store.getters['product/allProducts']);
const categories = computed(() => store.getters['product/allCategories']);
const pagination = computed(() => store.getters['product/productPagination']);
const loading = computed(() => store.getters['product/isLoading']);

function formatPrice(price) {
  return (price / 100).toFixed(2);
}

function goCreate() {
  router.push({ name: 'ProductCreate' });
}

function goDetail(id) {
  router.push({ name: 'ProductDetail', params: { id } });
}

function handleSearch() {
  currentPage.value = 1;
  store.dispatch('product/setFilters', {
    keyword: searchKeyword.value,
    category: filterCategory.value,
    sort: filterSort.value
  });
}

function resetFilters() {
  searchKeyword.value = '';
  filterCategory.value = '';
  filterSort.value = 'created_desc';
  currentPage.value = 1;
  store.dispatch('product/clearFilters');
}

function handlePageChange(page) {
  store.dispatch('product/setPage', page);
}

async function handleAddToCart(product) {
  try {
    await store.dispatch('cart/addToCart', { product, quantity: 1 });
    ElMessage.success('已加入购物车');
  } catch (error) {
    ElMessage.error('加入购物车失败');
  }
}

onMounted(async () => {
  await Promise.all([
    store.dispatch('product/fetchProducts'),
    store.dispatch('product/fetchCategories')
  ]);
});
</script>

<style scoped>
.product-list-container {
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

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
}

.product-grid {
  min-height: 400px;
}

.grid-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.product-card {
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.product-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.product-image {
  position: relative;
  height: 200px;
  overflow: hidden;
}

.image {
  width: 100%;
  height: 100%;
}

.image-slot {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  background: #f5f7fa;
  color: #909399;
  font-size: 48px;
}

.category-tag {
  position: absolute;
  top: 8px;
  right: 8px;
}

.product-info {
  padding: 16px;
}

.product-name {
  margin: 0 0 8px;
  font-size: 16px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-desc {
  margin: 0 0 12px;
  font-size: 13px;
  color: #909399;
  height: 40px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.product-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.product-price {
  font-size: 20px;
  font-weight: 600;
  color: #f56c6c;
}

.product-stock {
  font-size: 13px;
  color: #909399;
}

.add-cart-btn {
  width: 100%;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style>
