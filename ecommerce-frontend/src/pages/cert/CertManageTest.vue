<template>
  <div class="cert-manage-test-page">
    <!-- 页面标题 -->
    <div class="page-title">证书获取 & 有效性测试</div>

    <!-- 一、证书获取区域 -->
    <div class="card-wrapper">
      <div class="card-title">1. 证书获取</div>
      <div class="form-group">
        <!-- 方式1：调用接口获取证书 -->
        <div class="form-item">
          <label>接口获取证书（按证书ID）：</label>
          <input
            v-model="certId"
            type="text"
            placeholder="输入证书ID"
            class="input-box"
          />
          <button @click="getCertByApi" :disabled="loading">
            {{ loading ? '获取中...' : '调用接口获取' }}
          </button>
        </div>

        <!-- 方式2：本地上传证书文件（PEM格式） -->
        <div class="form-item">
          <label>本地上传证书：</label>
          <input
            type="file"
            accept=".pem,.crt,.cer"
            @change="uploadCertFile"
            class="file-input"
          />
        </div>

        <!-- 证书内容展示 -->
        <div class="cert-content">
          <label>当前证书内容（PEM格式）：</label>
          <textarea
            v-model="certContent"
            placeholder="获取/上传证书后展示内容..."
            class="cert-textarea"
          ></textarea>
        </div>
      </div>
    </div>

    <!-- 二、证书测试区域 -->
    <div class="card-wrapper">
      <div class="card-title">2. 证书测试（解析+有效性验证）</div>
      <div class="form-group">
        <button @click="testCert" :disabled="!certContent || testLoading">
          {{ testLoading ? '测试中...' : '开始测试证书' }}
        </button>

        <!-- 测试结果展示 -->
        <div v-if="testResult" class="test-result">
          <div class="result-title">证书解析&测试结果：</div>
          <pre class="result-content">{{ JSON.stringify(testResult, null, 2) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { X509 } from 'jsrsasign' // 证书解析核心库

export default {
  name: 'CertManageTest',
  data() {
    return {
      // 证书获取相关
      certId: '', // 证书ID（接口获取用）
      certContent: '', // 证书PEM内容
      loading: false, // 获取证书加载状态
      // 证书测试相关
      testLoading: false, // 测试证书加载状态
      testResult: null, // 测试结果
    }
  },
  methods: {
    // 方式1：调用后端接口获取证书
    async getCertByApi() {
      if (!this.certId) {
        alert('请输入证书ID！')
        return
      }
      this.loading = true
      try {
        // 替换为你的后端获取证书接口地址
        const res = await axios.get(`/api/v1/cert/download/${cert.id}`)
        if (res.data.code === 200 && res.data.data) {
          this.certContent = res.data.data.certPem // 假设接口返回证书PEM内容
          alert('证书获取成功！')
        } else {
          alert('证书获取失败：' + res.data.msg)
        }
      } catch (err) {
        console.error('获取证书接口报错：', err)
        alert('接口调用失败：' + err.message)
      } finally {
        this.loading = false
      }
    },

    // 方式2：本地上传证书文件
    uploadCertFile(e) {
      const file = e.target.files[0]
      if (!file) return
      const reader = new FileReader()
      reader.onload = (event) => {
        this.certContent = event.target.result // 读取文件内容为PEM格式
        alert('证书文件上传成功！')
      }
      reader.readAsText(file) // 以文本形式读取证书文件
    },

    // 测试证书（解析+有效性验证）
    testCert() {
      this.testLoading = true
      this.testResult = null
      try {
        // 1. 解析X.509证书
        const x509 = new X509()
        x509.readCertPEM(this.certContent) // 解析PEM格式证书

        // 2. 提取核心信息
        const certInfo = {
          证书版本: x509.version,
          证书序列号: x509.getSerialNumberHex(),
          颁发者: x509.getIssuerString(),
          使用者: x509.getSubjectString(),
          有效期起始: x509.getNotBefore(),
          有效期结束: x509.getNotAfter(),
          公钥算法: x509.getPublicKeyAlgorithm(),
          公钥长度: x509.getPublicKeySize(),
          签名算法: x509.getSignatureAlgorithm(),
        }

        // 3. 验证证书有效性（有效期）
        const now = new Date()
        const notBefore = new Date(x509.getNotBefore())
        const notAfter = new Date(x509.getNotAfter())
        const isExpired = now > notAfter
        const isNotYetValid = now < notBefore
        const isValid = !isExpired && !isNotYetValid

        // 4. 组装测试结果
        this.testResult = {
          基础信息: certInfo,
          有效性验证: {
            证书是否过期: isExpired,
            证书是否未到生效时间: isNotYetValid,
            证书当前是否有效: isValid,
          },
        }
      } catch (err) {
        console.error('证书测试报错：', err)
        this.testResult = {
          测试失败: '证书解析/验证出错',
          错误信息: err.message,
        }
      } finally {
        this.testLoading = false
      }
    },
  },
}
</script>

<style scoped>
.cert-manage-test-page {
  max-width: 1200px;
  margin: 20px auto;
  padding: 0 20px;
  font-family: "Microsoft YaHei", sans-serif;
}

.page-title {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 20px;
  color: #333;
}

.card-wrapper {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 20px;
  margin-bottom: 20px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 15px;
  color: #409eff;
  border-left: 3px solid #409eff;
  padding-left: 10px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-item {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.input-box {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  width: 200px;
  outline: none;
}

.input-box:focus {
  border-color: #409eff;
}

button {
  padding: 8px 16px;
  background: #409eff;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

button:hover:not(:disabled) {
  background: #66b1ff;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.file-input {
  padding: 5px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.cert-content {
  width: 100%;
}

.cert-textarea {
  width: 100%;
  min-height: 150px;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: vertical;
  outline: none;
}

.cert-textarea:focus {
  border-color: #409eff;
}

.test-result {
  margin-top: 10px;
}

.result-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #333;
}

.result-content {
  background: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  min-height: 200px;
  white-space: pre-wrap;
  word-wrap: break-word;
  color: #333;
}
</style>
