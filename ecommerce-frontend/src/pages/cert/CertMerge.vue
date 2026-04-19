<template>
  <div class="cert-page">
    <h2>证书获取 & 有效性测试（合并版）</h2>
    <div class="btn-group">
      <button @click="getCert" :disabled="loading">
        {{ loading ? "获取中..." : "1. 获取服务器证书" }}
      </button>
      <button @click="testCert" :disabled="!certContent || testLoading">
        {{ testLoading ? "测试中..." : "2. 测试证书有效性" }}
      </button>
    </div>

    <textarea v-model="certContent" placeholder="证书内容会展示在这里" rows="12"></textarea>

    <div v-if="result" class="result-box">
      <h3>测试结果</h3>
      <p>状态码：{{result.code}}</p>
      <p>校验结果：{{result.valid ? "✅ 证书有效" : "❌ 证书无效"}}</p>
      <p>详情：{{result.msg}}</p>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  data(){
    return {
      certContent: "",
      loading: false,
      testLoading: false,
      result: null
    }
  },
  methods:{
    // 调用后端获取证书接口
    async getCert(){
      this.loading = true
      this.result = null
      try{
        const res = await axios.get("/api/cert/get")
        if(res.data.code === 200){
          this.certContent = res.data.data.cert
          alert("✅ 证书获取成功")
        }
      }catch(err){
        alert("❌ 获取失败："+ err)
      }finally{
        this.loading = false
      }
    },
    // 调用后端测试证书接口
    async testCert(){
      this.testLoading = true
      try{
        const res = await axios.post("/api/cert/test", {cert: this.certContent})
        this.result = res.data
      }catch(err){
        alert("❌ 测试失败："+ err)
      }finally{
        this.testLoading = false
      }
    }
  }
}
</script>

<style scoped>
.cert-page{max-width: 900px;margin:30px auto;padding:20px}
h2{text-align:center;margin-bottom:20px}
.btn-group{display:flex;gap:15px;margin-bottom:20px}
button{padding:10px 20px;border:none;border-radius:4px;color:#fff;cursor:pointer}
button:first-child{background:#409eff}
button:last-child{background:#67c23a}
button:disabled{background:#ccc}
textarea{width:100%;padding:12px;border:1px solid #ddd;border-radius:6px}
.result-box{margin-top:20px;padding:15px;background:#f0f9eb;border-radius:6px}
</style>
