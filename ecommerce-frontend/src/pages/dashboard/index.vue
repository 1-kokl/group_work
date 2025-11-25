<template>
  <section class="dashboard-page">
    <header class="dashboard-header">
      <h1>仪表盘</h1>
      <p>这里可以查看整体运营概况，功能待接入后端数据。</p>
    </header>

    <div class="dashboard-grid">
      <div class="dashboard-card">
        <h2>总订单</h2>
        <p class="dashboard-number">0</p>
        <small>等待后端接口联调</small>
      </div>
      <div class="dashboard-card">
        <h2>今日销售额</h2>
        <p class="dashboard-number">￥0</p>
        <small>等待后端接口联调</small>
      </div>
      <div class="dashboard-card">
        <h2>活跃用户</h2>
        <p class="dashboard-number">0</p>
        <small>等待后端接口联调</small>
      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: 'DashboardPage'
};
</script>

<style scoped>
.dashboard-page {
  padding: 24px;
}

.dashboard-header h1 {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 600;
}

.dashboard-header p {
  margin: 0;
  color: #666;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin-top: 24px;
}

.dashboard-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 6px 20px rgba(15, 26, 58, 0.06);
}

.dashboard-card h2 {
  margin: 0 0 12px;
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.dashboard-number {
  margin: 0 0 4px;
  font-size: 28px;
  font-weight: 600;
  color: #409eff;
}

small {
  color: #999;
}
</style>


