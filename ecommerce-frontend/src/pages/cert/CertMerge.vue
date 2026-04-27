<template>
  <div class="cert-merge">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>📜 证书合并工具</span>
          <el-tag type="info">二合一证书生成</el-tag>
        </div>
      </template>

      <el-form label-width="120px">
        <!-- CA证书 -->
        <el-form-item label="CA根证书">
          <el-input
            v-model="caCert"
            type="textarea"
            :rows="6"
            placeholder="粘贴CA根证书内容（PEM格式）..."
            :disabled="loading"
          />
          <el-button
            size="small"
            style="margin-top: 8px"
            @click="loadCACert"
            :loading="loadingCA"
          >
            自动加载CA证书
          </el-button>
        </el-form-item>

        <!-- 用户证书 -->
        <el-form-item label="用户证书">
          <el-input
            v-model="userCert"
            type="textarea"
            :rows="6"
            placeholder="粘贴用户证书内容（PEM格式）..."
            :disabled="loading"
          />
        </el-form-item>

        <!-- 操作按钮 -->
        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            @click="mergeCertificates"
            :disabled="!caCert || !userCert"
          >
            🔗 合并证书
          </el-button>
          <el-button
            type="success"
            @click="testUserCert"
            :loading="testLoading"
            :disabled="!userCert"
          >
            ✅ 测试证书
          </el-button>
          <el-button @click="resetForm">
            🔄 重置
          </el-button>
        </el-form-item>

        <!-- 测试结果 -->
        <el-alert
          v-if="testResult"
          :title="testResult.message"
          :type="testResult.valid ? 'success' : 'error'"
          show-icon
          :closable="false"
          style="margin-bottom: 20px"
        />

        <!-- 合并结果 -->
        <el-divider v-if="mergedCert" content-position="left">
          合并结果
        </el-divider>

        <el-form-item v-if="mergedCert" label="合并后证书">
          <el-input
            v-model="mergedCert"
            type="textarea"
            :rows="10"
            readonly
          />
          <div style="margin-top: 10px">
            <el-button
              type="success"
              size="small"
              @click="downloadMergedCert"
            >
              💾 下载证书文件
            </el-button>
            <el-button
              size="small"
              @click="copyToClipboard"
            >
              📋 复制到剪贴板
            </el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 使用说明 -->
    <el-card style="margin-top: 20px">
      <template #header>
        <span>📖 使用说明</span>
      </template>
      <ol style="padding-left: 20px; line-height: 2">
        <li>点击"自动加载CA证书"或手动粘贴CA根证书内容</li>
        <li>粘贴用户证书内容（可通过证书管理页面获取）</li>
        <li>点击"测试证书"验证用户证书格式是否正确</li>
        <li>点击"合并证书"生成包含完整证书链的二合一证书</li>
        <li>下载或复制合并后的证书文件使用</li>
      </ol>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import http from '@/services/http';
import { ElMessage } from 'element-plus';

const caCert = ref('');
const userCert = ref('');
const mergedCert = ref('');
const loading = ref(false);
const loadingCA = ref(false);
const testLoading = ref(false);
const testResult = ref(null);

async function loadCACert() {
  loadingCA.value = true;
  try {
    const res = await http.get('/api/cert/ca');
    caCert.value = res.data || res;
    ElMessage.success('✅ CA证书加载成功');
  } catch (err) {
    ElMessage.error('❌ 加载失败：' + (err.message || '未知错误'));
  } finally {
    loadingCA.value = false;
  }
}

async function testUserCert() {
  if (!userCert.value.trim()) {
    ElMessage.warning('⚠️ 请先输入用户证书内容');
    return;
  }

  testLoading.value = true;
  testResult.value = null;

  try {
    const res = await http.post('/api/cert/test', {
      cert: userCert.value.trim()
    });
    const data = res.data || res;
    testResult.value = {
      valid: data.valid,
      message: data.message || (data.valid ? '证书格式有效' : '证书格式无效')
    };

    if (data.valid) {
      ElMessage.success('✅ 证书测试通过');
    } else {
      ElMessage.warning('⚠️ 证书格式可能有问题');
    }
  } catch (err) {
    ElMessage.error('❌ 测试失败：' + (err.message || '未知错误'));
  } finally {
    testLoading.value = false;
  }
}

async function mergeCertificates() {
  if (!caCert.value.trim() || !userCert.value.trim()) {
    ElMessage.warning('⚠️ CA证书和用户证书都不能为空');
    return;
  }

  loading.value = true;
  mergedCert.value = '';
  testResult.value = null;

  try {
    const res = await http.post('/api/cert/merge', {
      ca_cert: caCert.value.trim(),
      user_cert: userCert.value.trim()
    });

    const data = res.data || res;
    mergedCert.value = data.merged_cert;
    ElMessage.success('✅ 证书合并成功');
  } catch (err) {
    ElMessage.error('❌ 合并失败：' + (err.message || '未知错误'));
  } finally {
    loading.value = false;
  }
}

function downloadMergedCert() {
  if (!mergedCert.value) {
    ElMessage.warning('⚠️ 没有可下载的证书');
    return;
  }

  const blob = new Blob([mergedCert.value], { type: 'application/x-pem-file' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `merged_certificate_${new Date().getTime()}.pem`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  ElMessage.success('✅ 证书文件已下载');
}

async function copyToClipboard() {
  if (!mergedCert.value) {
    ElMessage.warning('⚠️ 没有可复制的内容');
    return;
  }

  try {
    await navigator.clipboard.writeText(mergedCert.value);
    ElMessage.success('✅ 已复制到剪贴板');
  } catch (err) {
    ElMessage.error('❌ 复制失败：' + err.message);
  }
}

function resetForm() {
  caCert.value = '';
  userCert.value = '';
  mergedCert.value = '';
  testResult.value = null;
  ElMessage.info('🔄 表单已重置');
}
</script>

<style scoped>
.cert-merge {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  font-size: 16px;
}

:deep(.el-textarea__inner) {
  font-family: 'Courier New', monospace;
  font-size: 12px;
}
</style>




