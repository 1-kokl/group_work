## 组件使用与规范

### 1. 目录分层

```
src/components/
├── layout/      # 布局与导航（Header、Sidebar、MobileNav 等）
├── forms/       # 表单相关小组件（如自定义输入、校验提示）
└── common/      # 可跨页面复用的基础组件（LoadingOverlay、SkeletonCard 等）
```

页面级组件存放于 `src/pages/**`，仅通过路由懒加载引用，内部可组合多个通用组件。

### 2. 命名约定

- 文件与导出使用 PascalCase，如 `LoadingOverlay.vue`。
- props 采用 `kebab-case` 在模板中绑定，类型在 `<script setup>` 内通过 `defineProps` 声明。
- 事件命名遵循 `update:modelValue`、`submit` 等标准。

### 3. 样式与主题

- 使用 Element Plus 自带主题 + 自定义 SCSS（后续可按需扩展）。
- 局部样式默认 `scoped`；全局变量、Breakpoints 建议集中在 `src/styles/variables.scss`（待补充）。
- Mobile 端使用 `clamp` 调整字体（参考 `App.vue`），基于媒体查询处理布局响应。

### 4. 重要组件说明

| 组件 | 目录 | 作用 |
| ---- | ---- | ---- |
| `AppHeader.vue` | `components/layout` | 顶部导航，内置用户菜单、角色显示、注销逻辑 |
| `AppSidebar.vue` | `components/layout` | 桌面端侧边导航，根据角色过滤菜单 |
| `MobileNav.vue` | `components/layout` | 移动端底部导航 |
| `AppBreadcrumb.vue` | `components/layout` | 基于 `route.matched` 的面包屑渲染 |
| `LoadingOverlay.vue` | `components/common` | 全局加载遮罩，配合 Vuex `globalLoading` 使用 |
| `GlobalStatus.vue` | `components/common` | 全局错误提示 + LoadingOverlay 统一入口 |
| `SkeletonCard.vue` | `components/common` | 列表/表单加载骨架 |
| `ErrorBoundary.vue` | `components/common` | 捕获子组件渲染错误，提供降级 UI |

### 5. 测试要求

- 所有公共组件需在 `tests/unit` 中补充至少一个快照或行为测试。
- 使用 `@testing-library/vue` 时以用户行为驱动测试（如 `findByRole`、`fireEvent`）。
- 对需要网络请求的组件，通过 MSW mock 或 Vuex action mock 进行隔离。

### 6. 开发建议

1. **表单组件**：封装重复的验证逻辑，统一引入 `security.js` 中的校验函数。
2. **异步组件**：若体积较大，可使用 `defineAsyncComponent` + `Suspense` 懒加载，配合全局 Skeleton 提升体验。
3. **无障碍**：使用语义化标签与 `aria-*` 属性，保证屏幕阅读器可用。
4. **国际化预留**：为文本信息提供可替换接口（后续如引入 i18n，可集中替换）。

后续新增组件请在本文件补充说明，包含使用场景、props/事件说明、依赖关系等，便于团队协作与维护。

