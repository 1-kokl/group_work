<template>
  <el-card class="skeleton-card" shadow="never">
    <el-skeleton animated :count="count">
      <template #template>
        <el-skeleton-item variant="p" style="width: 60%; margin-bottom: 12px" />
        <el-skeleton-item variant="text" />
        <el-skeleton-item variant="text" />
        <el-skeleton-item variant="text" style="width: 80%" />
      </template>
    </el-skeleton>
  </el-card>
</template>

<script setup>
defineProps({
  count: {
    type: Number,
    default: 1
  }
});
</script>

<style scoped>
.skeleton-card {
  border-radius: 16px;
  padding: 18px;
  background: linear-gradient(135deg, #f9fafb, #ffffff);
}
</style>

