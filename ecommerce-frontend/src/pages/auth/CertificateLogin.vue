<template>
  <div class="auth-container">
    <div class="auth-card">
      <header class="auth-header">
        <h1>证书强认证登录</h1>
        <p>请选择已安装的数字证书完成身份验证</p>
      </header>

      <!-- 证书选择区域 -->
      <div class="cert-select-section" v-if="!certSelected">
        <el-alert
          type="info"
          show-icon
          title="温馨提示"
          description="请确保已安装平台颁发的数字证书，且证书未过期/吊销"
          class="cert-alert"
        />

        <el-button
          type="primary"
          class="cert-detect-btn"
          :loading="detectingCert"
          @click="detectCertificates"
        >
          <el-icon><Key /></el-icon>
          检测本地数字证书
        </el-button>

        <!-- 证书列表 -->
        <el-select
          v-if="certList.length > 0"
          v-model="selectedCert"
          placeholder="请选择要使用的证书"
          class="cert-select"
          @change="onCertSelect"
        >
          <el-option
            v-for="cert in certList"
            :key="cert.serialNumber"
            :label="`${cert.subjectCN} (有效期至: ${cert.validTo})`"
            :value="cert"
          />
        </el-select>

        <el-empty
          v-if="certList.length === 0 && !detectingCert && certDetected"
          description="未检测到有效数字证书，请先安装平台颁发的证书"
        />
      </div>

      <!-- 证书验证区域 -->
      <div class="cert-verify-section" v-else>
        <div class="cert-info-card">
          <h3>选中证书信息</h3>
          <ul class="cert-info-list">
            <li><span class="label">证书主体：</span>{{ selectedCert.subjectCN }}</li>
            <li><span class="label">证书序列号：</span>{{ selectedCert.serialNumber }}</li>
            <li><span class="label">颁发机构：</span>{{ selectedCert.issuerCN }}</li>
            <li><span class="label">有效期至：</span>{{ selectedCert.validTo }}</li>
          </ul>
        </div>

        <el-button
          type="primary"
          class="cert-verify-btn"
          :loading="verifyingCert"
          @click="verifyCertificate"
        >
          <el-icon><Shield /></el-icon>
          验证证书并登录
        </el-button>

        <el-button
          type="text"
          class="cert-back-btn"
          @click="resetCertSelection"
        >
          重新选择证书
        </el-button>
      </div>

      <!-- 错误提示 -->
      <el-alert
        v-if="errorMessage"
        class="auth-alert"
        type="error"
        show-icon
        :closable="false"
        :title="errorMessage"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router'; // 正确
import { useStore } from 'vuex'; // 保留（仅导入一次）
import { ElMessage } from 'element-plus';
import { Key, Shield } from '@element-plus/icons-vue';
import { sanitizeInput } from '../../utils/security';
import { requestWithCert } from '../../services/certAuth'; // 证书认证请求工具

// 状态管理
const detectingCert = ref(false);
const certDetected = ref(false);
const certSelected = ref(false);
const verifyingCert = ref(false);
const errorMessage = ref('');
const certList = ref([]); // 检测到的证书列表
const selectedCert = ref(null);

const router = useRouter();
const store = useStore();

/**
 * 模拟检测本地数字证书（实际需对接浏览器/系统证书接口）
 * 生产环境需使用 WebCrypto API/平台提供的证书插件
 */
const detectCertificates = async () => {
  try {
    detectingCert.value = true;
    errorMessage.value = '';

    // 实际场景：调用证书插件/浏览器 API 获取本地证书列表
    // 此处为模拟数据，需替换为真实证书检测逻辑
    const mockCertList = [
      {
        subjectCN: '电商平台-张三-运营管理员',
        serialNumber: '1234567890ABCDEF',
        issuerCN: '电商平台CA中心',
        validFrom: '2024-01-01',
        validTo: '2025-01-01',
        thumbprint: 'mock-thumbprint-1'
      },
      {
        subjectCN: '电商平台-李四-财务',
        serialNumber: '0987654321FEDCBA',
        issuerCN: '电商平台CA中心',
        validFrom: '2024-02-01',
        validTo: '2025-02-01',
        thumbprint: 'mock-thumbprint-2'
      }
    ];

    certList.value = mockCertList;
    certDetected.value = true;
  } catch (error) {
    errorMessage.value = '证书检测失败：' + (error.message || '请检查证书驱动/插件');
    certList.value = [];
  } finally {
    detectingCert.value = false;
  }
};

/**
 * 选择证书后回调
 */
const onCertSelect = (cert) => {
  if (cert) {
    certSelected.value = true;
    errorMessage.value = '';
  }
};

/**
 * 重置证书选择
 */
const resetCertSelection = () => {
  certSelected.value = false;
  selectedCert.value = null;
  errorMessage.value = '';
};

/**
 * 验证证书并完成登录
 */
const verifyCertificate = async () => {
  if (!selectedCert.value) {
    errorMessage.value = '请先选择有效的数字证书';
    return;
  }

  try {
    verifyingCert.value = true;
    errorMessage.value = '';

    // 1. 证书合法性校验（前端预校验）
    const now = new Date();
    const validTo = new Date(selectedCert.value.validTo);
    if (validTo < now) {
      throw new Error('所选证书已过期，请联系管理员更新');
    }

    // 2. 调用证书认证接口（携带证书指纹/签名）
    const loginRes = await requestWithCert({
      certThumbprint: selectedCert.value.thumbprint,
      certSerial: selectedCert.value.serialNumber,
      // 可选：添加证书签名的随机串，防止重放攻击
      nonce: Math.random().toString(36).substring(2, 15)
    });

    // 3. 登录成功处理（同原有登录逻辑）
    await store.dispatch('auth/loginWithCert', {
      certInfo: selectedCert.value,
      token: loginRes.token,
      refreshToken: loginRes.refreshToken
    });

    ElMessage.success('证书验证成功，已完成强认证登录');
    router.replace({ name: 'Navigation' });
  } catch (error) {
    errorMessage.value =
      error.message ||
      '证书验证失败：证书无效/已吊销/权限不足，请联系管理员';
  } finally {
    verifyingCert.value = false;
  }
};
</script>

<style scoped>
/* 复用原有登录页样式基础，新增证书相关样式 */
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0f5ff 0%, #fefefe 100%);
  padding: 24px;
}

.auth-card {
  width: 100%;
  max-width: 520px;
  background: #fff;
  border-radius: 16px;
  padding: 32px 36px;
  box-shadow: 0 20px 40px -24px rgba(59, 87, 255, 0.45);
}

.auth-header {
  text-align: center;
  margin-bottom: 24px;
}

.auth-header h1 {
  margin: 0;
  font-size: 26px;
  color: #1f2937;
}

.auth-header p {
  margin: 8px 0 0;
  color: #6b7280;
  font-size: 14px;
}

/* 证书选择区域 */
.cert-select-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.cert-alert {
  margin-bottom: 8px;
}

.cert-detect-btn {
  height: 44px;
  font-size: 16px;
}

.cert-select {
  margin-top: 8px;
}

/* 证书验证区域 */
.cert-verify-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.cert-info-card {
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
}

.cert-info-card h3 {
  margin: 0 0 12px;
  font-size: 16px;
  color: #1f2937;
}

.cert-info-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.cert-info-list .label {
  font-weight: 600;
  color: #374151;
}

.cert-verify-btn {
  height: 44px;
  font-size: 16px;
}

.cert-back-btn {
  color: #6b7280;
  margin: 0 auto;
}

.auth-alert {
  margin-top: 16px;
}

/* 响应式适配 */
@media (max-width: 600px) {
  .auth-card {
    padding: 24px;
    border-radius: 12px;
  }
}
</style>

