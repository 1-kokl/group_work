<template>
  <div class="cert-center">
    <!-- 返回按钮 -->
    <el-button
      type="text"
      class="back-btn"
      @click="goBackToNavigation"
    >
      <el-icon><ArrowLeft /></el-icon>
      返回系统导航
    </el-button>

    <!-- 顶部标题 -->
    <el-card class="header-card" shadow="hover">
      <div class="page-header">
        <h1>🔐 证书管理中心</h1>
        <p>一站式证书获取、测试、合并与管理</p>
      </div>
    </el-card>

    <!-- 功能标签页 -->
    <el-tabs v-model="activeTab" type="border-card" class="cert-tabs">

      <!-- Tab 1: 获取我的证书 -->
      <el-tab-pane label="📥 获取证书" name="fetch">
        <el-card shadow="never">
          <template #header>
            <div class="tab-header">
              <span>获取我的用户证书</span>
              <el-tag type="success">推荐</el-tag>
            </div>
          </template>

          <el-alert
            title="提示"
            type="info"
            description="如果还没有证书，请先点击“签发新证书”；如果已有证书，点击“获取我的证书”下载"
            show-icon
            :closable="false"
            style="margin-bottom: 20px"
          />

          <div class="button-group">
            <el-button
              type="warning"
              size="large"
              @click="issueNewCert"
              :loading="issueLoading"
              icon="Plus"
            >
              签发新证书
            </el-button>

            <el-button
              type="primary"
              size="large"
              @click="fetchMyCert"
              :loading="fetchLoading"
              icon="Download"
            >
              获取我的证书
            </el-button>
          </div>

          <!-- 证书展示区域 -->
          <el-divider v-if="myCertContent" content-position="left">
            证书内容
          </el-divider>

          <el-input
            v-if="myCertContent"
            v-model="myCertContent"
            type="textarea"
            :rows="8"
            readonly
            placeholder="证书将显示在这里..."
          />

          <div v-if="myCertContent" class="action-buttons">
            <el-button type="success" @click="downloadMyCert" icon="Download">
              下载证书文件
            </el-button>
            <el-button @click="copyMyCert" icon="CopyDocument">
              复制到剪贴板
            </el-button>
            <el-button type="warning" @click="testMyCert" icon="Check">
              测试证书有效性
            </el-button>
          </div>

          <!-- 证书信息 -->
          <el-descriptions
            v-if="certInfo"
            title="证书详细信息"
            :column="2"
            border
            style="margin-top: 20px"
          >
            <el-descriptions-item label="用户名">
              {{ certInfo.username }}
            </el-descriptions-item>
            <el-descriptions-item label="序列号">
              {{ certInfo.serial_number }}
            </el-descriptions-item>
            <el-descriptions-item label="生效时间">
              {{ formatTime(certInfo.not_before) }}
            </el-descriptions-item>
            <el-descriptions-item label="过期时间">
              <span :class="{ 'text-danger': isExpired(certInfo.not_after) }">
                {{ formatTime(certInfo.not_after) }}
              </span>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-tab-pane>

      <!-- Tab 2: 测试证书 -->
      <el-tab-pane label="🧪 测试证书" name="test">
        <el-card shadow="never">
          <template #header>
            <div class="tab-header">
              <span>证书有效性测试</span>
              <el-tag type="warning">验证工具</el-tag>
            </div>
          </template>

          <el-form label-width="100px">
            <el-form-item label="证书内容">
              <el-input
                v-model="testCertContent"
                type="textarea"
                :rows="8"
                placeholder="粘贴要测试的证书内容（PEM格式）..."
              />
              <div class="form-tip">
                <el-link type="primary" @click="pasteFromClipboard">
                  从剪贴板粘贴
                </el-link>
              </div>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                @click="testCertificate"
                :loading="testLoading"
                :disabled="!testCertContent"
                icon="Check"
              >
                开始测试
              </el-button>
              <el-button @click="clearTest" icon="RefreshLeft">
                清空
              </el-button>
            </el-form-item>
          </el-form>

          <!-- 测试结果 -->
          <el-alert
            v-if="testResult"
            :title="testResult.valid ? '✅ 测试通过' : '❌ 测试失败'"
            :type="testResult.valid ? 'success' : 'error'"
            :description="testResult.message"
            show-icon
            :closable="false"
            style="margin-top: 20px"
          />

          <!-- 测试详情 -->
          <el-card
            v-if="testResult && testResult.details"
            shadow="never"
            style="margin-top: 20px"
          >
            <template #header>测试详情</template>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="格式验证">
                <el-tag :type="testResult.details.format ? 'success' : 'danger'">
                  {{ testResult.details.format ? '通过' : '失败' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="有效期">
                {{ testResult.details.validity || '未知' }}
              </el-descriptions-item>
              <el-descriptions-item label="颁发者">
                {{ testResult.details.issuer || '未知' }}
              </el-descriptions-item>
              <el-descriptions-item label="主题">
                {{ testResult.details.subject || '未知' }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-card>
      </el-tab-pane>

      <!-- Tab 3: 合并证书 -->
      <el-tab-pane label="🔗 合并证书" name="merge">
        <el-card shadow="never">
          <template #header>
            <div class="tab-header">
              <span>证书链合并工具</span>
              <el-tag type="info">二合一生成</el-tag>
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
                icon="Upload"
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
              <el-link
                type="primary"
                style="margin-top: 8px; display: block"
                @click="useMyCertForMerge"
              >
                使用我刚才获取的证书
              </el-link>
            </el-form-item>

            <!-- 操作按钮 -->
            <el-form-item>
              <el-button
                type="primary"
                :loading="loading"
                @click="mergeCertificates"
                :disabled="!caCert || !userCert"
                icon="Link"
              >
                合并证书
              </el-button>
              <el-button
                type="success"
                @click="testUserCertBeforeMerge"
                :loading="testLoading"
                :disabled="!userCert"
                icon="Check"
              >
                先测试证书
              </el-button>
              <el-button @click="resetMergeForm" icon="RefreshLeft">
                重置
              </el-button>
            </el-form-item>

            <!-- 测试结果 -->
            <el-alert
              v-if="mergeTestResult"
              :title="mergeTestResult.message"
              :type="mergeTestResult.valid ? 'success' : 'error'"
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
              <div class="action-buttons">
                <el-button
                  type="success"
                  size="small"
                  @click="downloadMergedCert"
                  icon="Download"
                >
                  下载证书文件
                </el-button>
                <el-button
                  size="small"
                  @click="copyMergedCert"
                  icon="CopyDocument"
                >
                  复制到剪贴板
                </el-button>
              </div>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- Tab 4: 下载根证书 -->
      <el-tab-pane label="📜 根证书" name="root">
        <el-card shadow="never">
          <template #header>
            <div class="tab-header">
              <span>CA 根证书下载</span>
              <el-tag type="info">信任基础</el-tag>
            </div>
          </template>

          <el-alert
            title="什么是根证书？"
            type="info"
            description="根证书用于验证平台下发的所有证书的有效性。下载后请安装到系统的受信任根证书颁发机构中。"
            show-icon
            :closable="false"
            style="margin-bottom: 20px"
          />

          <el-button
            type="primary"
            size="large"
            @click="downloadRootCert"
            :loading="rootCertLoading"
            icon="Download"
          >
            下载根证书（PEM格式）
          </el-button>

          <el-divider content-position="left">各系统安装说明</el-divider>

          <el-timeline>
            <el-timeline-item
              v-for="(item, index) in installSteps"
              :key="index"
              :timestamp="item.os"
              placement="top"
            >
              <el-card>
                <p>{{ item.steps }}</p>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 使用说明卡片 -->
    <el-card class="help-card" shadow="hover">
      <template #header>
        <span>💡 快速上手指南</span>
      </template>
      <el-steps :active="currentStep" finish-status="success" align-center>
        <el-step title="获取证书" description="在第一个标签页获取你的用户证书" />
        <el-step title="测试证书" description="验证证书格式是否正确" />
        <el-step title="合并证书" description="与CA证书合并生成完整证书链" />
        <el-step title="安装使用" description="下载并安装到浏览器或系统" />
      </el-steps>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import http from '@/services/http';
import { ElMessage } from 'element-plus';
import { Download, Check, CopyDocument, RefreshLeft, Link, Upload, ArrowLeft } from '@element-plus/icons-vue';

const router = useRouter();

// 标签页控制
const activeTab = ref('fetch');
const currentStep = ref(0);

// 获取证书相关
const fetchLoading = ref(false);
const issueLoading = ref(false);
const myCertContent = ref('');
const certInfo = ref(null);

// 测试证书相关
const testCertContent = ref('');
const testLoading = ref(false);
const testResult = ref(null);

// 合并证书相关
const caCert = ref('');
const userCert = ref('');
const mergedCert = ref('');
const loading = ref(false);
const loadingCA = ref(false);
const mergeTestResult = ref(null);

// 根证书相关
const rootCertLoading = ref(false);

// 安装步骤说明
const installSteps = [
  {
    os: 'Windows',
    steps: '双击证书文件 → 安装证书 → 选择"本地计算机" → 选择"受信任的根证书颁发机构" → 完成'
  },
  {
    os: 'macOS',
    steps: '双击证书文件 → 打开钥匙串访问 → 选择"登录" → 找到证书 → 右键"显示简介" → 展开"信任" → 设置为"始终信任"'
  },
  {
    os: 'Linux',
    steps: '复制证书到 /usr/local/share/ca-certificates/ → 执行 sudo update-ca-certificates → 重启应用'
  }
];

/**
 * 返回系统导航页面
 */
function goBackToNavigation() {
  router.push({ name: 'Navigation' });
}

// ==================== 签发证书功能 ====================

async function issueNewCert() {
  const username = prompt('请输入要签发证书的用户名：');

  if (!username || !username.trim()) {
    ElMessage.warning('⚠️ 用户名不能为空');
    return;
  }

  issueLoading.value = true;
  try {
    console.log('[签发证书] 开始签发，用户名:', username.trim());

    const res = await http.post('/api/cert/issue', {
      username: username.trim()
    });

    console.log('[签发证书] 原始响应:', res);
    console.log('[签发证书] res.code:', res?.code);
    console.log('[签发证书] res.data:', res?.data);

    // http.js 已经返回了 response.data，所以 res 就是后端的整个 JSON 响应
    const responseData = res;

    console.log('[签发证书] 解析后的数据:', responseData);
    console.log('[签发证书] responseData.code:', responseData?.code);
    console.log('[签发证书] responseData.data:', responseData?.data);

    if (responseData.code === 200 && responseData.data) {
      const certData = responseData.data;

      console.log('[签发证书] 证书数据:', certData);
      console.log('[签发证书] 证书长度:', certData.certificate?.length);
      console.log('[签发证书] 私钥长度:', certData.private_key?.length);

      // 显示证书信息
      certInfo.value = {
        username: certData.username,
        serial_number: certData.serial_number,
        not_before: certData.not_before,
        not_after: certData.not_after
      };

      myCertContent.value = certData.certificate;

      ElMessage.success('✅ 证书签发成功！');
      currentStep.value = 1;

      // 自动下载证书
      setTimeout(() => {
        downloadCertWithKey(certData);
      }, 500);
    } else {
      console.error('[签发证书] 失败，响应数据:', responseData);
      throw new Error(responseData.msg || '签发失败');
    }
  } catch (err) {
    console.error('[签发证书] 错误详情:', err);
    console.error('[签发证书] 错误状态码:', err.status);
    console.error('[签发证书] 错误消息:', err.message);

    let errorMsg = '签发失败';

    if (err.status === 401) {
      errorMsg = '请先登录后再签发证书';
    } else if (err.status === 500) {
      errorMsg = '服务器内部错误：' + (err.message || '未知错误');
    } else if (err.status === 400) {
      errorMsg = '请求参数错误：' + (err.message || '用户名格式不正确');
    } else {
      errorMsg = '签发失败：' + (err.message || '未知错误');
    }

    ElMessage.error('❌ ' + errorMsg);
  } finally {
    issueLoading.value = false;
  }
}

function downloadCertWithKey(certData) {
  const fullCert = `-----BEGIN PRIVATE KEY-----
${certData.private_key.match(/-----BEGIN PRIVATE KEY-----([\s\S]*?)-----END PRIVATE KEY-----/)?.[1] || ''}
-----END PRIVATE KEY-----

${certData.certificate}`;

  const blob = new Blob([fullCert], { type: 'application/x-pem-file' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${certData.username}_certificate_${new Date().getTime()}.pem`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  ElMessage.success('✅ 证书文件已下载，请妥善保管！');
}

// ==================== 获取证书功能 ====================

async function fetchMyCert() {
  fetchLoading.value = true;
  try {
    const res = await http.get('/api/cert/get');
    const data = res.data || res;

    if (data.cert) {
      myCertContent.value = data.cert;
      certInfo.value = {
        username: '当前用户',
        serial_number: 'N/A',
        not_before: new Date().toISOString(),
        not_after: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString()
      };

      ElMessage.success('✅ 证书获取成功！');
      currentStep.value = 1;

      // 自动切换到测试标签页
      setTimeout(() => {
        activeTab.value = 'test';
        testCertContent.value = myCertContent.value;
      }, 1000);
    } else {
      ElMessage.warning('⚠️ 未找到证书信息，可能还未签发证书');
    }
  } catch (err) {
    ElMessage.error('❌ 获取失败：' + (err.message || '未知错误'));
  } finally {
    fetchLoading.value = false;
  }
}

function downloadMyCert() {
  if (!myCertContent.value) {
    ElMessage.warning('⚠️ 没有可下载的证书');
    return;
  }

  const blob = new Blob([myCertContent.value], { type: 'application/x-pem-file' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `user_certificate_${new Date().getTime()}.pem`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  ElMessage.success('✅ 证书已下载');
}

async function copyMyCert() {
  if (!myCertContent.value) {
    ElMessage.warning('⚠️ 没有可复制的内容');
    return;
  }

  try {
    await navigator.clipboard.writeText(myCertContent.value);
    ElMessage.success('✅ 已复制到剪贴板');
  } catch (err) {
    ElMessage.error('❌ 复制失败：' + err.message);
  }
}

async function testMyCert() {
  if (!myCertContent.value) {
    ElMessage.warning('⚠️ 请先获取证书');
    return;
  }

  activeTab.value = 'test';
  testCertContent.value = myCertContent.value;
  await testCertificate();
}

// ==================== 测试证书功能 ====================

async function testCertificate() {
  if (!testCertContent.value.trim()) {
    ElMessage.warning('⚠️ 请先输入证书内容');
    return;
  }

  testLoading.value = true;
  testResult.value = null;

  try {
    const res = await http.post('/api/cert/test', {
      cert: testCertContent.value.trim()
    });
    const data = res.data || res;

    testResult.value = {
      valid: data.valid,
      message: data.message || (data.valid ? '证书格式有效' : '证书格式无效'),
      details: {
        format: data.valid,
        validity: '需要后端提供详细信息',
        issuer: '需要后端提供详细信息',
        subject: '需要后端提供详细信息'
      }
    };

    if (data.valid) {
      ElMessage.success('✅ 证书测试通过');
      currentStep.value = 2;
    } else {
      ElMessage.warning('⚠️ 证书格式可能有问题');
    }
  } catch (err) {
    testResult.value = {
      valid: false,
      message: '测试失败：' + (err.message || '未知错误')
    };
    ElMessage.error('❌ 测试失败：' + (err.message || '未知错误'));
  } finally {
    testLoading.value = false;
  }
}

async function pasteFromClipboard() {
  try {
    const text = await navigator.clipboard.readText();
    testCertContent.value = text;
    ElMessage.success('✅ 已从剪贴板粘贴');
  } catch (err) {
    ElMessage.error('❌ 读取剪贴板失败：' + err.message);
  }
}

function clearTest() {
  testCertContent.value = '';
  testResult.value = null;
  ElMessage.info('🔄 已清空');
}

// ==================== 合并证书功能 ====================

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

function useMyCertForMerge() {
  if (!myCertContent.value) {
    ElMessage.warning('⚠️ 请先在"获取证书"标签页获取你的证书');
    activeTab.value = 'fetch';
    return;
  }

  userCert.value = myCertContent.value;
  ElMessage.success('✅ 已使用你的证书');
}

async function testUserCertBeforeMerge() {
  if (!userCert.value.trim()) {
    ElMessage.warning('⚠️ 请先输入用户证书内容');
    return;
  }

  testLoading.value = true;
  mergeTestResult.value = null;

  try {
    const res = await http.post('/api/cert/test', {
      cert: userCert.value.trim()
    });
    const data = res.data || res;

    mergeTestResult.value = {
      valid: data.valid,
      message: data.message || (data.valid ? '证书格式有效' : '证书格式无效')
    };

    if (data.valid) {
      ElMessage.success('✅ 证书测试通过，可以合并');
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
  mergeTestResult.value = null;

  try {
    const res = await http.post('/api/cert/merge', {
      ca_cert: caCert.value.trim(),
      user_cert: userCert.value.trim()
    });

    const data = res.data || res;
    mergedCert.value = data.merged_cert;
    ElMessage.success('✅ 证书合并成功');
    currentStep.value = 3;
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

async function copyMergedCert() {
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

function resetMergeForm() {
  caCert.value = '';
  userCert.value = '';
  mergedCert.value = '';
  mergeTestResult.value = null;
  ElMessage.info('🔄 表单已重置');
}

// ==================== 根证书下载 ====================

async function downloadRootCert() {
  rootCertLoading.value = true;
  try {
    const res = await http.get('/api/cert/ca');
    const certContent = res.data || res;

    const blob = new Blob([certContent], { type: 'application/x-pem-file' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'root_ca_certificate.pem';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    ElMessage.success('✅ 根证书已下载');
  } catch (err) {
    ElMessage.error('❌ 下载失败：' + (err.message || '未知错误'));
  } finally {
    rootCertLoading.value = false;
  }
}

// ==================== 工具函数 ====================

function formatTime(isoString) {
  if (!isoString) return 'N/A';
  const date = new Date(isoString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}


function isExpired(expiredAt) {
  if (!expiredAt) return false;
  return new Date(expiredAt) < new Date();
}

</script>

<style scoped>
.cert-center {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header-card {
  margin-bottom: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.page-header h1 {
  margin: 0 0 8px;
  font-size: 28px;
}

.page-header p {
  margin: 0;
  opacity: 0.9;
  font-size: 14px;
}

.cert-tabs {
  margin-bottom: 20px;
}

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.action-buttons {
  margin-top: 10px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.button-group {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.form-tip {
  margin-top: 8px;
  font-size: 12px;
}

.text-danger {
  color: #f56c6c;
  font-weight: 600;
}

.help-card {
  margin-top: 20px;
}

:deep(.el-textarea__inner) {
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

:deep(.el-timeline-item__content) {
  width: 100%;
}

.back-btn {
  margin-bottom: 20px;
}

.back-btn {
  margin-bottom: 20px;
}
</style>



