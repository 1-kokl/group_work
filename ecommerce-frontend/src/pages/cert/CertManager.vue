<template>
  <div class="cert-manager-page">
    <el-card shadow="hover">
      <div class="card-header">
        <h2>证书管理</h2>
        <el-button
          type="primary"
          icon="el-icon-circle-plus"
          @click="$router.push('/cert/generate-csr')"
        >
          申请新证书
        </el-button>
      </div>

      <el-table
        :data="certList"
        border
        stripe
        v-loading="loading"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="证书ID" width="120" />
        <el-table-column prop="cn" label="通用名称" min-width="200" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'active' ? 'success' : 'danger'">
              {{ scope.row.status === 'active' ? '有效' : '已吊销' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="validFrom" label="生效时间" width="180" />
        <el-table-column prop="validTo" label="过期时间" width="180">
          <template #default="scope">
            <span :class="{ 'text-danger': isExpired(scope.row.validTo) }">
              {{ scope.row.validTo }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button
              type="text"
              icon="el-icon-download"
              @click="handleDownloadCert(scope.row)"
              v-if="scope.row.status === 'active'"
            >
              下载证书
            </el-button>
            <el-button
              type="text"
              icon="el-icon-refresh"
              @click="handleRenewCert(scope.row)"
              v-if="scope.row.status === 'active'"
            >
              续期
            </el-button>
            <el-button
              type="text"
              icon="el-icon-delete"
              @click="handleRevokeCert(scope.row)"
              v-if="scope.row.status === 'active'"
              style="color: #f56c6c"
            >
              吊销
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="certList.length"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :current-page="currentPage"
        :page-sizes="[10, 20, 50]"
        :page-size="pageSize"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        style="margin-top: 20px; text-align: right"
      >
      </el-pagination>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { getCertList, revokeCert, renewCert } from '@/services/api/certAPI'; // 需自行封装接口

// 状态管理
const loading = ref(false);
const certList = ref([]);
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);
const selectedCerts = ref([]);

// 页面加载时获取证书列表
onMounted(() => {
  fetchCertList();
});

// 获取证书列表
const fetchCertList = async () => {
  try {
    loading.value = true;
    const res = await getCertList({
      page: currentPage.value,
      size: pageSize.value
    });
    certList.value = res.data.list;
    total.value = res.data.total;
  } catch (error) {
    ElMessage.error('获取证书列表失败：' + error.message);
  } finally {
    loading.value = false;
  }
};

// 分页/条数变更
const handleSizeChange = (val) => {
  pageSize.value = val;
  fetchCertList();
};
const handleCurrentChange = (val) => {
  currentPage.value = val;
  fetchCertList();
};

// 选择证书
const handleSelectionChange = (val) => {
  selectedCerts.value = val;
};

// 判断证书是否过期
const isExpired = (validTo) => {
  return new Date(validTo) < new Date();
};

// 下载证书
const handleDownloadCert = (cert) => {
  // 调用下载接口（示例）
  const link = document.createElement('a');
  link.href = `/api/v1/cert/download/${cert.id}`;
  link.download = `${cert.cn}-cert.pem`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  ElMessage.success('证书下载成功');
};

// 证书续期
const handleRenewCert = async (cert) => {
  try {
    await ElMessageBox.confirm('确认续期该证书？续期后有效期将延长1年', '提示', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    });
    await renewCert(cert.id);
    ElMessage.success('证书续期成功');
    fetchCertList(); // 刷新列表
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('续期失败：' + error.message);
    }
  }
};

// 吊销证书
const handleRevokeCert = async (cert) => {
  try {
    await ElMessageBox.confirm('确认吊销该证书？吊销后将无法恢复', '警告', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'error'
    });
    await revokeCert(cert.id);
    ElMessage.success('证书吊销成功');
    fetchCertList(); // 刷新列表
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('吊销失败：' + error.message);
    }
  }
};
</script>

<style scoped>
.cert-manager-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.text-danger {
  color: #f56c6c;
}
</style>

