# 核心框架文件模板

本文件包含 src/ 下项目启动所需的最小文件集。

---

## src/main.ts

```ts
import { createApp } from 'vue'

import App from './App.vue'
import router from './router'

import './assets/css/tailwind.css'

const app = createApp(App)

app.use(router)

app.mount('#app')
```

---

## src/App.vue

```vue
<script setup lang="ts">
// 根组件
</script>

<template>
  <router-view />
</template>
```

---

## src/router/index.ts

```ts
import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/Home.vue'),
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router
```

---

## src/views/Home.vue

生成时将 `项目名称` 替换为用户配置的 `projectTitle` 值。

```vue
<script setup lang="ts">
// 首页
</script>

<template>
  <div>
    <h1>项目名称</h1>
    <router-view />
  </div>
</template>
```
