<template>
  <div class="root-cert-page">
    <el-card title="根证书下载" shadow="hover">
      <div class="cert-desc">
        <p>根证书用于验证平台下发的服务端证书有效性，请下载后安装到信任列表。</p>
        <p>支持格式：PEM（通用）、CRT（Windows）</p>
      </div>
      <el-button
        type="primary"
        icon="el-icon-download"
        @click="handleDownloadRootCert"
        class="download-btn"
      >
        下载根证书（PEM格式）
      </el-button>
      <el-divider content-position="left">使用说明</el-divider>
      <el-table :data="usageList" border>
        <el-table-column prop="os" label="操作系统" width="120" />
        <el-table-column prop="steps" label="安装步骤" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { downloadRootCert } from '@/utils/crypto';

// 根证书下载
const handleDownloadRootCert = () => {
  downloadRootCert();
};

// 使用说明列表
const usageList = [
  {
    os: 'Windows',
    steps: '1. 双击证书文件 → 安装证书 → 本地计算机 → 受信任的根证书颁发机构 → 完成'
  },
  {
    os: 'macOS',
    steps: '1. 双击证书文件 → 钥匙串访问 → 登录 → 证书 → 右键信任 → 始终信任'
  },
  {
    os: 'Linux',
    steps: '1. 复制到 /usr/local/share/ca-certificates/ → 执行 update-ca-certificates'
  }
];
</script>

<style scoped>
.root-cert-page {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.cert-desc {
  margin-bottom: 20px;
  color: #666;
  line-height: 1.6;
}

.download-btn {
  margin-bottom: 20px;
}
</style>

