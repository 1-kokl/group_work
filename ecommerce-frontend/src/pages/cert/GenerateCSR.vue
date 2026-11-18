<template>
  <div class="generate-csr-page">
    <el-card title="生成证书签名请求（CSR）" shadow="hover">
      <el-form :model="csrForm" :rules="csrRules" ref="csrFormRef" label-width="100px">
        <el-form-item label="通用名称(CN)" prop="cn">
          <el-input v-model="csrForm.cn" placeholder="如：api.ecommerce.com" />
        </el-form-item>
        <el-form-item label="组织(O)" prop="org">
          <el-input v-model="csrForm.org" placeholder="如：Ecommerce Inc." />
        </el-form-item>
        <el-form-item label="国家(C)" prop="country">
          <el-input v-model="csrForm.country" placeholder="如：CN" maxlength="2" />
        </el-form-item>
        <el-form-item label="省份(ST)" prop="state">
          <el-input v-model="csrForm.state" placeholder="如：Guangdong" />
        </el-form-item>
        <el-form-item label="城市(L)" prop="city">
          <el-input v-model="csrForm.city" placeholder="如：Shenzhen" />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            @click="handleGenerateCSR"
            :loading="loading"
            icon="el-icon-key"
          >
            生成CSR + 密钥对
          </el-button>
          <el-button
            type="success"
            @click="handleDownloadCSR"
            :disabled="!csrContent"
            icon="el-icon-download"
            style="margin-left: 10px"
          >
            下载CSR文件
          </el-button>
        </el-form-item>
      </el-form>

      <el-divider content-position="left">生成结果（仅临时展示）</el-divider>
      <el-tabs v-if="csrContent || privateKeyPem || publicKeyPem">
        <el-tab-pane label="CSR内容">
          <el-input v-model="csrContent" type="textarea" rows="10" readonly />
        </el-tab-pane>
        <el-tab-pane label="公钥(PEM)">
          <el-input v-model="publicKeyPem" type="textarea" rows="10" readonly />
        </el-tab-pane>
        <el-tab-pane label="私钥(PEM)" warning>
          <p style="color: #f56c6c; margin-bottom: 10px">⚠️ 私钥仅前端临时生成，请勿泄露！建议本地备份后刷新页面清空</p>
          <el-input v-model="privateKeyPem" type="textarea" rows="10" readonly />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import {
  generateRSAKeyPair,
  generateCSR,
  exportPublicKeyToPEM,
  exportPrivateKeyToPEM,
  downloadCSR
} from '@/utils/crypto';

// 表单状态
const csrFormRef = ref(null);
const loading = ref(false);
const csrContent = ref('');
const publicKeyPem = ref('');
const privateKeyPem = ref('');

// CSR表单
const csrForm = reactive({
  cn: '',
  org: '',
  country: '',
  state: '',
  city: ''
});

// 表单校验规则
const csrRules = {
  cn: [{ required: true, message: '请输入通用名称', trigger: 'blur' }],
  org: [{ required: true, message: '请输入组织名称', trigger: 'blur' }],
  country: [{ required: true, message: '请输入国家代码', trigger: 'blur' }]
};

// 生成CSR和密钥对
const handleGenerateCSR = async () => {
  try {
    await csrFormRef.value.validate();
    loading.value = true;

    // 1. 生成RSA密钥对
    const keyPair = await generateRSAKeyPair();

    // 2. 构造CSR主题信息
    const subject = {
      CN: csrForm.cn,
      O: csrForm.org,
      C: csrForm.country,
      ST: csrForm.state,
      L: csrForm.city
    };

    // 3. 生成CSR
    const csr = await generateCSR(keyPair, subject);
    csrContent.value = csr;

    // 4. 导出公钥/私钥（仅展示，生产环境建议仅下载不展示）
    publicKeyPem.value = await exportPublicKeyToPEM(keyPair.publicKey);
    privateKeyPem.value = await exportPrivateKeyToPEM(keyPair.privateKey);

    ElMessage.success('CSR和密钥对生成成功！');
  } catch (error) {
    ElMessage.error('生成失败：' + error.message);
  } finally {
    loading.value = false;
  }
};

// 下载CSR文件
const handleDownloadCSR = () => {
  if (!csrContent.value) {
    ElMessage.warning('请先生成CSR');
    return;
  }
  const filename = `${csrForm.cn || 'cert'}-request.csr`;
  downloadCSR(csrContent.value, filename);
};
</script>

<style scoped>
.generate-csr-page {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.el-textarea {
  --el-textarea-input-font-size: 12px;
}
</style>

