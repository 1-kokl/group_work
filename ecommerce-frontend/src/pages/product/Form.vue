<template>
  <div class="product-form-container">
    <div class="page-header">
      <h2>{{ isEdit ? '编辑商品' : '发布商品' }}</h2>
    </div>

    <el-card>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        status-icon
      >
        <el-form-item label="商品名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="请输入商品名称"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="商品分类" prop="category">
          <el-select v-model="form.category" placeholder="请选择分类" style="width: 100%">
            <el-option
              v-for="cat in categories"
              :key="cat.id"
              :label="cat.name"
              :value="cat.name"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="价格" prop="price">
          <el-input-number
            v-model="form.priceDisplay"
            :min="0.01"
            :precision="2"
            :controls="false"
            style="width: 200px"
          >
            <template #append>元</template>
          </el-input-number>
          <span class="form-tip">输入后自动转换为分提交给后端</span>
        </el-form-item>

        <el-form-item label="库存" prop="stock">
          <el-input-number
            v-model="form.stock"
            :min="0"
            :max="999999"
          />
        </el-form-item>

        <el-form-item label="商品图片" prop="image_url">
          <el-input
            v-model="form.image_url"
            placeholder="请输入图片链接"
          >
            <template #append>
              <el-button @click="previewImage">预览</el-button>
            </template>
          </el-input>
          <div v-if="form.image_url" class="image-preview">
            <el-image
              :src="form.image_url"
              fit="contain"
              class="preview-img"
            >
              <template #error>
                <div class="preview-error">图片加载失败</div>
              </template>
            </el-image>
          </div>
        </el-form-item>

        <el-form-item label="商品描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="5"
            placeholder="请输入商品详细描述"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleSubmit">
            {{ isEdit ? '保存修改' : '立即发布' }}
          </el-button>
          <el-button @click="goBack">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useStore } from 'vuex';
import { ElMessage } from 'element-plus';

const route = useRoute();
const router = useRouter();
const store = useStore();

const formRef = ref(null);
const isEdit = computed(() => route.name === 'ProductEdit');
const productId = computed(() => route.params.id);
const categories = computed(() => store.getters['product/allCategories']);
const loading = computed(() => store.getters['product/isLoading']);

const form = reactive({
  name: '',
  category: '',
  priceDisplay: 0,
  price: 0,
  stock: 0,
  image_url: '',
  description: '',
  status: 1
});

const rules = {
  name: [
    { required: true, message: '请输入商品名称', trigger: 'blur' },
    { min: 2, max: 100, message: '名称长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  category: [
    { required: true, message: '请选择商品分类', trigger: 'change' }
  ],
  priceDisplay: [
    { required: true, message: '请输入价格', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value <= 0) {
          callback(new Error('价格必须大于0'));
        } else {
          callback();
        }
      },
      trigger: 'blur'
    }
  ],
  stock: [
    { required: true, message: '请输入库存', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value < 0) {
          callback(new Error('库存不能为负数'));
        } else {
          callback();
        }
      },
      trigger: 'blur'
    }
  ],
  description: [
    { required: true, message: '请输入商品描述', trigger: 'blur' }
  ]
};

function previewImage() {
  if (form.image_url) {
    window.open(form.image_url, '_blank');
  }
}

function goBack() {
  router.push({ name: 'ProductList' });
}

async function handleSubmit() {
  if (!formRef.value) return;

  try {
    await formRef.value.validate();

    const submitData = {
      name: form.name,
      category: form.category,
      price: Math.round(form.priceDisplay * 100),
      stock: form.stock,
      image_url: form.image_url,
      description: form.description,
      status: form.status
    };

    if (isEdit.value) {
      await store.dispatch('product/updateProduct', {
        id: productId.value,
        data: submitData
      });
      ElMessage.success('商品更新成功');
    } else {
      await store.dispatch('product/createProduct', submitData);
      ElMessage.success('商品发布成功');
    }

    router.push({ name: 'ProductList' });
  } catch (error) {
    if (error !== false) {
      ElMessage.error('提交失败，请检查表单');
    }
  }
}

function loadProductData(product) {
  form.name = product.name;
  form.category = product.category;
  form.priceDisplay = product.price / 100;
  form.price = product.price;
  form.stock = product.stock;
  form.image_url = product.image_url || '';
  form.description = product.description || '';
  form.status = product.status;
}

onMounted(async () => {
  await store.dispatch('product/fetchCategories');

  if (isEdit.value && productId.value) {
    try {
      await store.dispatch('product/fetchProductDetail', productId.value);
      const product = store.getters['product/currentProduct'];
      if (product) {
        loadProductData(product);
      }
    } catch (error) {
      ElMessage.error('加载商品信息失败');
      router.push({ name: 'ProductList' });
    }
  }
});
</script>

<style scoped>
.product-form-container {
  max-width: 800px;
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

.form-tip {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}

.image-preview {
  margin-top: 12px;
}

.preview-img {
  width: 200px;
  height: 200px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.preview-error {
  width: 200px;
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  color: #909399;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}
</style>
