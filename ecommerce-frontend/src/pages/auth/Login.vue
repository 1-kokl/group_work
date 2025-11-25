<template>
  <div class="auth-container">
    <div class="auth-card">
      <header class="auth-header">
        <h1>欢迎回来</h1>
        <p>请输入账号信息登录系统</p>
      </header>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        status-icon
        label-position="top"
        class="auth-form"
        @keyup.enter="handleSubmit"
      >
        <el-form-item prop="identifier" label="用户名 / 邮箱">
          <el-input
            v-model.trim="form.identifier"
            placeholder="请输入用户名或邮箱"
            autocomplete="username"
            clearable
            :disabled="loading"
          >
            <template #prepend>
              <el-icon><UserFilled /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item prop="password" label="密码">
          <el-input
            v-model="form.password"
            placeholder="请输入密码"
            show-password
            autocomplete="current-password"
            :disabled="loading"
          >
            <template #prepend>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <div class="form-aux">
          <el-checkbox v-model="form.rememberMe" :disabled="loading">
            记住我
          </el-checkbox>

          <el-link type="primary" :underline="false" @click="goForgot">
            忘记密码？
          </el-link>
        </div>

        <el-alert
          v-if="errorMessage"
          class="auth-alert"
          type="error"
          show-icon
          :closable="false"
          :title="errorMessage"
        />

        <el-button
          type="primary"
          class="auth-submit"
          :loading="loading"
          :disabled="loading"
          @click="handleSubmit"
        >
          登录
        </el-button>

        <div class="form-footer">
          还没有账号？
          <el-link type="primary" :underline="false" @click="goRegister">
            立即注册
          </el-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useStore } from 'vuex';
import { ElMessage } from 'element-plus';
import { UserFilled, Lock } from '@element-plus/icons-vue';

import { sanitizeInput } from '../../utils/security';

const formRef = ref();
const loading = ref(false);
const errorMessage = ref('');

const store = useStore();
const router = useRouter();
const route = useRoute();

const form = reactive({
  identifier: '',
  password: '',
  rememberMe: false
});

const rules = {
  identifier: [
    { required: true, message: '请输入用户名或邮箱', trigger: 'blur' },
    {
      validator: (_, value, callback) => {
        const sanitized = sanitizeInput(value);
        if (sanitized !== value) {
          form.identifier = sanitized;
        }
        callback();
      },
      trigger: 'change'
    }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 位', trigger: 'blur' }
  ]
};

const redirectPath = computed(() => route.query.redirect || { name: 'Navigation' });

function goForgot() {
  ElMessage.info('请联系管理员或使用后台提供的找回方式。');
}

function goRegister() {
  router.push({ name: 'Register' });
}

async function handleSubmit() {
  if (!formRef.value) return;

  errorMessage.value = '';

  formRef.value.validate(async (valid) => {
    if (!valid) return;

    loading.value = true;
    try {
      await store.dispatch('auth/login', {
        identifier: sanitizeInput(form.identifier),
        password: form.password,
        remember: form.rememberMe
      });

      ElMessage.success('登录成功');
      router.replace(redirectPath.value);
    } catch (error) {
      const status =
        error?.status ||
        error?.response?.status ||
        error?.details?.status ||
        0;
      const rawMessage = error?.message || '';

      if (
        status === 401 ||
        rawMessage.includes('用户名或密码') ||
        rawMessage.includes('Unauthorized')
      ) {
        errorMessage.value = '用户名或密码错误，请重试。';
      } else if (error?.code === 'AUTH_LOCKED') {
        errorMessage.value = '账户已锁定，请联系管理员解锁。';
      } else {
        errorMessage.value = rawMessage || '登录失败，请稍后再试。';
      }

      if (!errorMessage.value || rawMessage.includes('网络连接异常')) {
        errorMessage.value = '登录失败，请检查账号信息或稍后再试。';
      }
    } finally {
      loading.value = false;
    }
  });
}

onMounted(() => {
  const saved = localStorage.getItem('auth.remember');
  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      form.identifier = parsed.identifier || '';
      form.rememberMe = true;
    } catch (error) {
      console.warn('解析记住的登录信息失败', error);
    }
  }
});
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0f5ff 0%, #fefefe 100%);
  padding: 24px;
}

.auth-card {
  width: 100%;
  max-width: 420px;
  background: #fff;
  border-radius: 16px;
  padding: 32px 36px;
  box-shadow: 0 20px 40px -24px rgba(59, 87, 255, 0.45);
}

.auth-header {
  text-align: center;
  margin-bottom: 24px;
}

.auth-header h1 {
  margin: 0;
  font-size: 26px;
  color: #1f2937;
}

.auth-header p {
  margin: 8px 0 0;
  color: #6b7280;
  font-size: 14px;
}

.auth-form {
  display: flex;
  flex-direction: column;
}

.form-aux {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.auth-alert {
  margin-bottom: 16px;
}

.auth-submit {
  width: 100%;
  height: 44px;
  font-size: 16px;
  margin-bottom: 12px;
}

.form-footer {
  text-align: center;
  color: #6b7280;
  font-size: 14px;
}

.captcha-col {
  display: flex;
  align-items: center;
  justify-content: center;
}

.captcha-image {
  width: 100%;
  height: 46px;
  border-radius: 8px;
  cursor: pointer;
  border: 1px solid #e5e7eb;
}

.captcha-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #6b7280;
  background-color: #f3f4f6;
  border-radius: 8px;
}

@media (max-width: 600px) {
  .auth-card {
    padding: 24px;
    border-radius: 12px;
  }

  .form-aux {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .captcha-col {
    margin-top: 4px;
  }
}
</style>

