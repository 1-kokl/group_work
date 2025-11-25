<template>
  <div class="auth-container">
    <div class="auth-card">
      <header class="auth-header">
        <h1>创建账户</h1>
        <p>注册成为电商平台的新用户</p>
      </header>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        status-icon
        class="auth-form"
        @keyup.enter="handleSubmit"
      >
        <el-form-item prop="username" label="用户名">
          <el-input
            v-model.trim="form.username"
            placeholder="请输入用户名"
            clearable
            :disabled="loading"
          >
            <template #prepend>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item prop="email" label="邮箱">
          <el-input
            v-model.trim="form.email"
            placeholder="请输入邮箱地址"
            clearable
            autocomplete="email"
            :disabled="loading"
          >
            <template #prepend>
              <el-icon><Message /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item prop="password" label="密码">
          <el-input
            v-model="form.password"
            placeholder="请输入密码"
            show-password
            autocomplete="new-password"
            :disabled="loading"
          >
            <template #prepend>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
          <div class="password-strength">
            <div class="strength-bar">
              <div
                v-for="(segment, index) in 5"
                :key="index"
                :class="[
                  'strength-segment',
                  index < passwordStrength.score ? strengthLevel : 'inactive'
                ]"
              />
            </div>
            <span class="strength-text">{{ passwordStrengthText }}</span>
          </div>
        </el-form-item>

        <el-form-item prop="confirmPassword" label="确认密码">
          <el-input
            v-model="form.confirmPassword"
            placeholder="请再次输入密码"
            show-password
            autocomplete="new-password"
            :disabled="loading"
          />
        </el-form-item>

        <el-form-item prop="phone" label="手机号">
          <el-input
            v-model.trim="form.phone"
            placeholder="请输入 11 位手机号"
            maxlength="11"
            :disabled="loading"
          >
            <template #prepend>
              <el-icon><Iphone /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item prop="agree">
          <el-checkbox v-model="form.agree" :disabled="loading">
            我已阅读并同意
            <el-link type="primary" :underline="false">《用户协议》</el-link>
            和
            <el-link type="primary" :underline="false">《隐私政策》</el-link>
          </el-checkbox>
        </el-form-item>

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
          注册并登录
        </el-button>

        <div class="form-footer">
          已有账号？
          <el-link type="primary" :underline="false" @click="goLogin">
            返回登录
          </el-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useStore } from 'vuex';
import { ElMessage } from 'element-plus';
import { User, Message, Lock, Iphone } from '@element-plus/icons-vue';

import {
  sanitizeInput,
  validatePasswordStrength,
  validatePhoneNumber,
  validateUsername
} from '../../utils/security';
import { debounceAsync } from '../../utils/perf';

const formRef = ref();
const loading = ref(false);
const errorMessage = ref('');
const usernameChecking = ref(false);

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  phone: '',
  agree: false
});

const router = useRouter();
const store = useStore();

const passwordStrength = computed(() =>
  validatePasswordStrength(form.password)
);

const strengthLevel = computed(() => {
  if (passwordStrength.value.score >= 4) return 'strong';
  if (passwordStrength.value.score >= 3) return 'medium';
  return 'weak';
});

const passwordStrengthText = computed(() => {
  if (!form.password) return '密码强度：--';
  return `密码强度：${strengthLevelLabel[strengthLevel.value]}`;
});

const strengthLevelLabel = {
  strong: '强',
  medium: '中',
  weak: '弱'
};

// 当前后端未实现 `/api/v1/user/check-username` 接口，这里暂时跳过远程校验，
// 只做前端格式校验，避免注册时出现“网络错误”。
const checkUsernameAvailability = debounceAsync(async () => true, 400);

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    {
      validator: async (_, value, callback) => {
        const sanitized = sanitizeInput(value);
        if (sanitized !== value) {
          form.username = sanitized;
        }

        const result = validateUsername(sanitized);
        if (result !== true) {
          callback(new Error(result));
          return;
        }

        if (!sanitized) {
          callback();
          return;
        }

        usernameChecking.value = true;
        try {
          const available = await checkUsernameAvailability(sanitized);
          if (!available) {
            callback(new Error('用户名已被占用，请更换一个。'));
          } else {
            callback();
          }
        } catch (error) {
          if (error?.message === 'REQUEST_DEBOUNCED') {
            return;
          }
          console.warn('检查用户名失败', error);
          callback(new Error('无法验证用户名，请稍后再试。'));
        } finally {
          usernameChecking.value = false;
        }
      },
      trigger: 'blur'
    }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: ['blur', 'change'] }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    {
      validator: (_, value, callback) => {
        const result = validatePasswordStrength(value);
        if (!result.valid) {
          callback(new Error(result.feedback[0] || '密码规则不符合要求'));
        } else {
          callback();
        }
      },
      trigger: 'change'
    }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_, value, callback) => {
        if (value !== form.password) {
          callback(new Error('两次输入的密码不一致'));
        } else {
          callback();
        }
      },
      trigger: ['blur', 'change']
    }
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    {
      validator: (_, value, callback) => {
        const sanitized = sanitizeInput(value);
        if (sanitized !== value) {
          form.phone = sanitized;
        }
        const result = validatePhoneNumber(sanitized);
        if (result !== true) {
          callback(new Error(result));
        } else {
          callback();
        }
      },
      trigger: ['blur', 'change']
    }
  ],
  agree: [
    {
      validator: (_, value, callback) => {
        if (!value) {
          callback(new Error('请先阅读并同意相关协议'));
        } else {
          callback();
        }
      },
      trigger: 'change'
    }
  ]
};

watch(
  () => form.password,
  () => {
    if (formRef.value) {
      formRef.value.validateField('confirmPassword').catch(() => {});
    }
  }
);

function goLogin() {
  router.push({ name: 'Login' });
}

async function handleSubmit() {
  if (!formRef.value || usernameChecking.value) return;

  errorMessage.value = '';

  formRef.value.validate(async (valid) => {
    if (!valid) return;

    loading.value = true;
    try {
      await store.dispatch('auth/register', {
        username: sanitizeInput(form.username),
        email: sanitizeInput(form.email),
        password: form.password,
        phone: sanitizeInput(form.phone)
      });

      await store.dispatch('auth/login', {
        identifier: sanitizeInput(form.username),
        password: form.password,
        remember: false
      });

      // 将注册信息写入本地用户资料（供个人中心展示）
      store.dispatch(
        'user/setProfile',
        {
          username: sanitizeInput(form.username),
          email: sanitizeInput(form.email),
          phone: sanitizeInput(form.phone),
          joinedAt: new Date().toLocaleString()
        },
        { root: true }
      );

      ElMessage.success('注册成功，已自动登录');
      router.replace({ name: 'Navigation' });
    } catch (error) {
      errorMessage.value =
        error?.message || '注册失败，请稍后再试。';
    } finally {
      loading.value = false;
    }
  });
}

</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #ecfdf5 0%, #ffffff 100%);
  padding: 24px;
}

.auth-card {
  width: 100%;
  max-width: 520px;
  background: #fff;
  border-radius: 16px;
  padding: 32px 40px;
  box-shadow: 0 20px 48px -24px rgba(16, 185, 129, 0.45);
}

.auth-header {
  text-align: center;
  margin-bottom: 24px;
}

.auth-header h1 {
  margin: 0;
  font-size: 26px;
  color: #064e3b;
}

.auth-header p {
  margin: 8px 0 0;
  color: #047857;
  font-size: 14px;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.password-strength {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.strength-bar {
  display: flex;
  gap: 4px;
  flex: 1;
}

.strength-segment {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background-color: #e5e7eb;
  transition: background-color 0.3s ease;
}

.strength-segment.weak {
  background-color: #f87171;
}

.strength-segment.medium {
  background-color: #facc15;
}

.strength-segment.strong {
  background-color: #34d399;
}

.strength-segment.inactive {
  background-color: #e5e7eb;
}

.strength-text {
  font-size: 12px;
  color: #6b7280;
  white-space: nowrap;
}

.auth-alert {
  margin: 12px 0;
}

.auth-submit {
  width: 100%;
  height: 44px;
  font-size: 16px;
  margin: 12px 0 8px;
}

.form-footer {
  text-align: center;
  color: #6b7280;
  font-size: 14px;
}

@media (max-width: 640px) {
  .auth-card {
    padding: 24px;
  }
}
</style>

