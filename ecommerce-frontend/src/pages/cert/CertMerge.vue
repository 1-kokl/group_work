<template>
  <div class="cert-merge">
    <h1>证书合并页面</h1>
  </div>
</template>

<script>
export default {
  name: 'CertMerge',
  data () {
    return {
      certContent: '',
      loading: false,
      testLoading: false,
      result: null
    }
  },
  methods: {
    async getCert () {
      this.loading = true
      this.result = null
      try {
        const res = await this.$axios.get('/api/cert/get')
        if (res.data.code !== 200) {
          throw new Error(res.data.msg || '证书获取接口返回异常')
        }
        this.certContent = res.data.data.cert
        alert('✅ 证书获取成功')
      } catch (err) {
        alert('❌ 获取失败：' + (err.message || err))
      } finally {
        this.loading = false
      }
    },
    async testCert () {
      if (!this.certContent.trim()) {
        alert('⚠️ 请先获取证书，或手动输入证书内容')
        return
      }
      this.testLoading = true
      try {
        const res = await this.$axios.post('/api/cert/test', { cert: this.certContent.trim() })
        this.result = res.data
      } catch (err) {
        alert('❌ 测试失败：' + (err.message || err))
      } finally {
        this.testLoading = false
      }
    }
  }
}
</script>

<style scoped>
.cert-merge {
  padding: 20px;
}
</style>
