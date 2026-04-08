import { createRouter, createWebHistory } from 'vue-router';
import store from '../store';
import RootCertDownload from '@/pages/cert/RootCertDownload.vue';
import CertManager from '@/pages/cert/CertManager.vue';
import GenerateCSR from '@/pages/cert/GenerateCSR.vue';


/**
 * 路由配置说明：
 * - component 使用懒加载（动态 import）以减小首屏体积
 * - meta.requiresAuth 控制登录访问
 * - meta.requiresGuest 控制未登录访问
 * - meta.roles 指定访问所需角色
 * - meta.title 用于动态更新页面标题
 */
const routes = [
  {
    path: '/',
    redirect: { name: 'Login' }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../pages/auth/Login.vue'),
    meta: {
      title: '登录',
      requiresGuest: true,
      hideLayout: true
    }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../pages/auth/Register.vue'),
    meta: {
      title: '注册',
      requiresGuest: true,
      hideLayout: true
    }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../pages/navigation/SystemNavigation.vue'),
    meta: {
      title: '系统导航',
      requiresAuth: true,
      roles: ['admin', 'operator', 'merchant']
    }
  },
  {
    path: '/navigation',
    name: 'Navigation',
    component: () => import('../pages/navigation/SystemNavigation.vue'),
    meta: {
      title: '系统导航',
      requiresAuth: true
    }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../pages/user/Profile.vue'),
    meta: {
      title: '个人中心',
      requiresAuth: true
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../components/common/NotFound.vue'),
    meta: {
      title: '页面不存在'
    }
  },
  {
    path: '/cert',
    component: RootCertDownload,
    meta: { requiresAuth: true, roles: ['admin'] }, // 需登录+管理员权限
    children: [
      { path: 'root', name: 'RootCertDownload', component: RootCertDownload },
      { path: 'manager', name: 'CertManager', component: CertManager },
      { path: 'generate-csr', name: 'GenerateCSR', component: GenerateCSR }
    ]
  }
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
  scrollBehavior: () => ({ top: 0 })
});

router.beforeEach((to, from, next) => {
  const isAuthenticated = store.getters['auth/isAuthenticated'];
  const currentUser = store.getters['auth/currentUser'];
  const requiresAuth = to.meta?.requiresAuth;
  const requiresGuest = to.meta?.requiresGuest;
  const requiredRoles = to.meta?.roles;

  if (to.meta?.title) {
    document.title = `${to.meta.title} - 电商运营系统`;
  }

  // 已登录用户访问仅访客页面（如登录、注册），自动跳转到仪表盘
  if (requiresGuest && isAuthenticated) {
    return next({ name: 'Navigation' });
  }

  // 未登录用户访问受保护页面，重定向到登录页并保留目标路径
  if (requiresAuth && !isAuthenticated) {
    return next({
      name: 'Login',
      query: { redirect: to.fullPath }
    });
  }

  // 做额外的角色校验，确保用户具备访问权限
  if (requiresAuth && requiredRoles?.length) {
    const userRoles =
      currentUser?.roles ||
      (currentUser?.role ? [currentUser.role] : []);
    const hasPermission = requiredRoles.some((role) => userRoles.includes(role));

    if (!hasPermission) {
      return next({ name: 'Navigation' });
    }
  }
  const token = localStorage.getItem('token');
  if (to.meta.requiresAuth && !localStorage.getItem('token')) {
    next('/login');
  } else {
    next();
  }

  return next();
});

export default router;

