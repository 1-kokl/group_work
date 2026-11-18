<template>
  <el-breadcrumb class="app-breadcrumb" separator="/">
    <el-breadcrumb-item
      v-for="(item, index) in breadcrumbItems"
      :key="item.path || index"
      :to="item.to"
    >
      <el-icon v-if="index === 0"><HomeFilled /></el-icon>
      <span>{{ item.meta?.title || item.name }}</span>
    </el-breadcrumb-item>
  </el-breadcrumb>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { HomeFilled } from '@element-plus/icons-vue';

const route = useRoute();

const breadcrumbItems = computed(() => {
  return route.matched
    .filter((item) => item.meta?.title)
    .map((item) => ({
      path: item.path,
      name: item.name,
      meta: item.meta,
      to:
        item.redirect || item.children?.length
          ? undefined
          : { name: item.name, params: route.params, query: route.query }
    }));
});
</script>

<style scoped>
.app-breadcrumb {
  padding: 12px 0;
  font-size: 13px;
  color: #6b7280;
}

.app-breadcrumb :deep(.el-breadcrumb__item .el-breadcrumb__inner.is-link) {
  font-weight: 500;
}
</style>

