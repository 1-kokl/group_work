<template>
  <div>
    <slot v-if="!hasError" />
    <div v-else class="error-fallback">
      <el-result
        icon="warning"
        title="页面出现错误"
        sub-title="我们已记录该问题，请稍后重试或刷新页面。"
      >
        <template #extra>
          <el-button type="primary" @click="handleReload">刷新页面</el-button>
          <el-button @click="handleReset">返回上一页</el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup>
import { onErrorCaptured, ref } from 'vue';
import { useRouter } from 'vue-router';

const hasError = ref(false);
const router = useRouter();

function handleReload() {
  window.location.reload();
}

function handleReset() {
  hasError.value = false;
  router.back();
}

onErrorCaptured((error, instance, info) => {
  console.error('[ErrorBoundary] 捕获到错误:', { error, instance, info });
  hasError.value = true;
  return false;
});
</script>

<style scoped>
.error-fallback {
  min-height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
</style>

