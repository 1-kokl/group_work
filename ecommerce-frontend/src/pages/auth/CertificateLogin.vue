<template>
  <div class="auth-container">
    <div class="auth-card">
      <!-- 返回按钮 -->
      <el-button
        type="text"
        class="back-btn"
        @click="goBackToNavigation"
      >
        <el-icon><ArrowLeft /></el-icon>
        返回系统导航
      </el-button>

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
          description="请上传平台颁发的数字证书文件（.pem/.crt格式），或从系统证书存储中选择"
          class="cert-alert"
        />

        <!-- 方式一：文件上传 -->
        <el-upload
          class="cert-upload"
          drag
          action="#"
          :auto-upload="false"
          :on-change="handleCertFileUpload"
          :before-upload="beforeCertUpload"
          accept=".pem,.crt,.cer,.der"
          :limit="1"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            拖拽证书文件到此处，或 <em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 .pem/.crt/.cer 格式，文件大小不超过 10KB
            </div>
          </template>
        </el-upload>

        <!-- 分隔线 -->
        <el-divider>或</el-divider>

        <!-- 方式二：检测系统证书 -->
        <el-button
          type="primary"
          class="cert-detect-btn"
          :loading="detectingCert"
          @click="detectCertificates"
        >
          <el-icon><Key /></el-icon>
          检测系统证书存储
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
          description="未检测到有效数字证书，请使用文件上传方式"
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
            <li><span class="label">指纹：</span>{{ selectedCert.thumbprint?.substring(0, 16) }}...</li>
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
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useStore } from 'vuex';
import { ElMessage } from 'element-plus';
import { Key, Shield, UploadFilled, ArrowLeft } from '@element-plus/icons-vue';
import http from '@/services/http';

// 状态管理
const detectingCert = ref(false);
const certDetected = ref(false);
const certSelected = ref(false);
const verifyingCert = ref(false);
const errorMessage = ref('');
const certList = ref([]);
const selectedCert = ref(null);
const uploadedCertContent = ref('');

const router = useRouter();
const store = useStore();

/**
 * 返回系统导航页面
 */
function goBackToNavigation() {
  router.push({ name: 'Navigation' });
}

/**
 * 文件上传前的验证
 */
function beforeCertUpload(file) {
  const isValidType = ['.pem', '.crt', '.cer', '.der'].some(ext =>
    file.name.toLowerCase().endsWith(ext)
  );
  const isLt10K = file.size / 1024 < 10;

  if (!isValidType) {
    ElMessage.error('只能上传 .pem/.crt/.cer/.der 格式的证书文件！');
    return false;
  }
  if (!isLt10K) {
    ElMessage.error('证书文件大小不能超过 10KB！');
    return false;
  }
  return true;
}

/**
 * 处理证书文件上传
 */
async function handleCertFileUpload(uploadFile) {
  try {
    errorMessage.value = '';
    const reader = new FileReader();

    reader.onload = async (e) => {
      const certContent = e.target.result;
      uploadedCertContent.value = certContent;

      // 解析证书基本信息
      const certInfo = await parseCertificateInfo(certContent);

      if (certInfo) {
        selectedCert.value = {
          ...certInfo,
          certContent: certContent,
          source: 'file'
        };
        certSelected.value = true;
        ElMessage.success('✅ 证书文件加载成功');
      } else {
        ElMessage.error('❌ 无法解析证书文件，请确认格式正确');
      }
    };

    reader.onerror = () => {
      ElMessage.error('❌ 读取证书文件失败');
    };

    reader.readAsText(uploadFile.raw);
  } catch (error) {
    errorMessage.value = '证书文件处理失败：' + error.message;
    ElMessage.error(errorMessage.value);
  }
}

/**
 * 解析证书信息（简化版，实际应使用 crypto API）
 */
async function parseCertificateInfo(certContent) {
  try {
    const cleanCert = certContent.trim();

    let subjectCN = '未知';
    const issuerCN = '未知';
    const serialNumber = '未知';

    const cnMatch = cleanCert.match(/CN\s*=\s*([^\n,]+)/);
    if (cnMatch) {
      subjectCN = cnMatch[1].trim();
    }

    const encoder = new TextEncoder();
    const data = encoder.encode(cleanCert);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const thumbprint = hashArray.map(b => b.toString(16).padStart(2, '0')).join('').toUpperCase();

    return {
      subjectCN: subjectCN,
      issuerCN: issuerCN,
      serialNumber: `FILE-${thumbprint.substring(0, 16)}`,
      thumbprint: thumbprint,
      validFrom: new Date().toISOString(),
      validTo: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString()
    };
  } catch (error) {
    console.error('解析证书失败:', error);
    return null;
  }
}

function extractCertificateOnly(content) {
  const certMatch = content.match(/-----BEGIN CERTIFICATE-----[\s\S]*?-----END CERTIFICATE-----/);
  if (certMatch) {
    return certMatch[0];
  }
  return content;
}

/**
 * 检测系统证书存储（需要浏览器支持）
 */
const detectCertificates = async () => {
  try {
    detectingCert.value = true;
    errorMessage.value = '';

    if ('credentials' in navigator && window.PublicKeyCredential) {
      console.log('浏览器支持 WebAuthn，但不支持直接读取 X.509 证书');
    }

    ElMessage.warning({
      message: '浏览器无法直接访问系统证书存储，请使用上方的文件上传方式',
      duration: 5000
    });

    certDetected.value = true;
    certList.value = [];
  } catch (error) {
    errorMessage.value = '证书检测失败：' + (error.message || '浏览器不支持此功能');
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
  uploadedCertContent.value = '';
  errorMessage.value = '';
  certDetected.value = false;
  certList.value = [];
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

    const now = new Date();
    const validTo = new Date(selectedCert.value.validTo);
    if (validTo < now) {
      throw new Error('所选证书已过期，请联系管理员更新');
    }

    const certContent = selectedCert.value.certContent || uploadedCertContent.value;

    console.log('=== 证书登录调试信息 ===');
    console.log('1. selectedCert:', selectedCert.value);
    console.log('2. certContent 长度:', certContent?.length);
    console.log('3. certContent 前200字符:', certContent?.substring(0, 200));

    const pureCert = extractCertificateOnly(certContent);

    console.log('4. pureCert 长度:', pureCert?.length);
    console.log('5. pureCert 前200字符:', pureCert?.substring(0, 200));
    console.log('6. pureCert 是否以 BEGIN 开头:', pureCert?.startsWith('-----BEGIN CERTIFICATE-----'));

    if (!pureCert || pureCert.length < 50) {
      throw new Error('证书内容无效或为空，请重新上传证书文件');
    }

    const requestData = {
      cert: pureCert,
      thumbprint: selectedCert.value.thumbprint,
      serial_number: selectedCert.value.serialNumber
    };

    console.log('7. 发送的请求数据:', {
      cert_length: requestData.cert.length,
      thumbprint: requestData.thumbprint,
      serial_number: requestData.serial_number
    });

    const loginRes = await http.post('/api/cert/cert-login', requestData, {
      skipAuthRefresh: true,
      suppressErrorEvent: true
    });

    console.log('8. 后端响应:', loginRes);

    // http.js 已经返回了 response.data，所以 loginRes 就是后端的 JSON 数据
    const responseData = loginRes;

    console.log('9. 解析后的数据:', responseData);
    console.log('10. code:', responseData?.code);
    console.log('11. data:', responseData?.data);

    if (responseData.code === 200 && responseData.data?.access_token) {
      await store.dispatch('auth/loginWithCert', {
        certInfo: selectedCert.value,
        token: responseData.data.access_token,
        refreshToken: responseData.data.refresh_token || null,
        expiresIn: responseData.data.expires_in || 7200
      });

      ElMessage.success('✅ 证书验证成功，已完成强认证登录');

      setTimeout(() => {
        router.replace({ name: 'CertCenter' });
      }, 500);
    } else {
      console.error('[证书登录] 失败原因:', responseData);
      throw new Error(responseData.msg || '证书验证失败');
    }
  } catch (error) {
    console.error('=== 证书登录错误详情 ===');
    console.error('错误对象:', error);
    console.error('错误消息:', error.message);
    console.error('错误状态码:', error.status);

    errorMessage.value =
      error.message ||
      '证书验证失败：证书无效/已吊销/权限不足，请联系管理员';
    ElMessage.error(errorMessage.value);
  } finally {
    verifyingCert.value = false;
  }
};
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0f5ff 0%, #fefefe 100%);
  padding: 24px;
}

.back-btn {
  position: absolute;
  top: 20px;
  left: 20px;
  font-size: 14px;
  color: #6b7280;
  z-index: 10;
}

.back-btn:hover {
  color: #3b57ff;
}

.auth-card {
  width: 100%;
  max-width: 560px;
  background: #fff;
  border-radius: 16px;
  padding: 32px 36px;
  box-shadow: 0 20px 40px -24px rgba(59, 87, 255, 0.45);
  position: relative;
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

.cert-select-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.cert-alert {
  margin-bottom: 8px;
}

.cert-upload {
  width: 100%;
}

.cert-upload :deep(.el-upload-dragger) {
  padding: 30px 20px;
}

.cert-detect-btn {
  height: 44px;
  font-size: 16px;
  width: 100%;
}

.cert-select {
  margin-top: 8px;
}

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

.cert-info-list li {
  font-size: 14px;
  word-break: break-all;
}

.cert-info-list .label {
  font-weight: 600;
  color: #374151;
  display: inline-block;
  min-width: 80px;
}

.cert-verify-btn {
  height: 44px;
  font-size: 16px;
  width: 100%;
}

.cert-back-btn {
  color: #6b7280;
  margin: 0 auto;
}

.auth-alert {
  margin-top: 16px;
}

@media (max-width: 600px) {
  .auth-card {
    padding: 24px;
    border-radius: 12px;
  }
}
</style>

