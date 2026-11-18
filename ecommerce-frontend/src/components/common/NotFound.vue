<template>
  <div class="not-found">
    <img
      class="not-found__illustration"
      src="https://cdn.svgporn.com/logos/vue.svg"
      alt="not found"
    />
    <h1>页面不存在</h1>
    <p>可能是链接失效，或者您没有权限访问该页面。</p>
    <router-link class="not-found__link" :to="{ name: 'Dashboard' }">
      返回仪表盘
    </router-link>
  </div>
</template>

<script>
export default {
  name: 'NotFound'
};
</script>

<style scoped>
.not-found {
  min-height: 60vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 32px 16px;
}

.not-found__illustration {
  width: 120px;
  height: 120px;
  opacity: 0.35;
  margin-bottom: 24px;
}

.not-found h1 {
  margin: 0 0 12px;
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}

.not-found p {
  margin: 0 0 24px;
  color: #73767a;
}

.not-found__link {
  color: #409eff;
  font-weight: 500;
}
</style>


