---
name: create-vue3-project
description: >
  基于星火AUTO（CIVI）开发平台基建规范，生成 Vue 3 + Rsbuild + Element Plus（按需引入）+ Tailwind CSS v4 前端子应用脚手架。
  包含完整的工程化配置：代码规范由 @hyluo2/spec-config 提供，Design Token 体系（--xha-* 前缀），开发代理由 @civi/url-plugin 统一管理。
  当用户要求创建 Vue 3 项目、初始化前端工程、搭建 Vue 项目骨架、新建项目、项目脚手架、vue3 模板时触发。
  即使用户没有明确说"Vue 3"，只要提到"新建前端项目"或"创建项目脚手架"，也应触发此 skill。
---

# Vue 3 项目生成器

基于星火AUTO开发平台现有基建规范，生成生产级 Vue 3 前端子应用。

## 第一步：收集配置

向用户确认以下配置项。使用中文交流，列出所有配置项和默认值，让用户确认或修改。

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `projectName` | 项目名称（目录名 + package.json name） | **必填** |
| `twPrefix` | Tailwind CSS 前缀（防止多子应用样式污染） | 项目名英文首字母简写，如 `notice-web` → `nw` |
| `projectTitle` | HTML 标题 & 错误提示标题 | 同 `projectName` |
| `outputDir` | 构建输出目录 | `dist` |
| `assetPrefix` | 静态资源前缀 | `/` |
| `port` | 开发服务器端口 | `8080` |
| `proxyPaths` | 需要代理的 API 路径前缀列表 | 无（注释状态，如 `['/api']`） |

**twPrefix 自动推导规则**：取项目名中每个 `-` 分隔单词的首字母，如：
- `notice-web` → `nw`
- `agent-container` → `ac`
- `ai-model-service` → `ams`
- `dashboard` → `d`

## 第二步：生成文件

确认配置后，按以下顺序使用 Write 工具逐文件生成。读取 `references/` 下的模板文件获取完整代码，替换 `{{变量名}}` 为用户配置值。

### 第 1 层：根配置文件

读取 `references/config-files.md`，生成以下文件：

1. `package.json` — 替换 `{{projectName}}`
2. `rsbuild.config.ts` — 替换 `{{projectTitle}}`、`{{outputDir}}`、`{{assetPrefix}}`、`{{port}}`、`{{proxyPaths}}`
3. `postcss.config.js`
4. `.eslintrc.js` — 使用 `@hyluo2/spec-config` 的 `getEslintConfig('vue3-ts')`
5. `.prettierrc.js` — 使用 `@hyluo2/spec-config` 的 `getPrettierConfig()`
6. `.lintstagedrc.cjs` — 使用 `@hyluo2/spec-config` 的 `getLintStagedConfig('vue3-ts')`
7. `.editorconfig`
8. `tsconfig.json`
9. `.env` — 替换 `{{port}}`
10. `.gitignore` — 替换 `{{outputDir}}`
11. `public/index.html`

### 第 2 层：样式文件

读取 `references/style-files.md`，生成以下文件：

12. `src/assets/css/tailwind.css` — 替换 `{{twPrefix}}`

### 第 3 层：核心框架文件

读取 `references/core-files.md`，生成以下文件：

13. `src/main.ts`
14. `src/App.vue`
15. `src/router/index.ts`
16. `src/views/Home.vue`

### 第 4 层：CLAUDE.md

17. `CLAUDE.md` — 项目开发指南，供 Claude Code 使用。根据项目实际配置生成，内容包括：

```markdown
# CLAUDE.md

## 项目概述

{{projectTitle}} 前端子应用，基于 Vue 3 + Vue Router 4 + Element Plus（按需引入），使用 Rsbuild 构建，Tailwind CSS v4 管理样式。
作为 micro-app 子应用接入父应用，登录和权限由父应用统一管理。

## 常用命令

- `pnpm serve` — 启动开发服务器（HTTPS）
- `pnpm build` — 生产构建（输出到 `{{outputDir}}/`）
- `pnpm lint` — ESLint 检查并自动修复

## 代码风格

- TypeScript strict 模式，ESLint 基于 airbnb-base + vue3-recommended + @typescript-eslint + prettier
- 行宽 150，缩进 2 空格，单引号，无分号，ES5 尾逗号
- 统一使用 Composition API + `<script setup>` 语法
- 状态管理使用 `ref`/`reactive` + composable，不使用 Pinia
- 代码规范由 `@hyluo2/spec-config` 提供（ESLint + Prettier + lint-staged 配置）
- Git Hooks 和提交校验由 monorepo 根目录统一管理，子项目无需关心
- 路径别名：`@` → `src/`

## 样式规范

- Tailwind CSS v4 工具类，前缀为 `{{twPrefix}}`（如 `{{twPrefix}}:flex`、`{{twPrefix}}:p-4`）
- Design Token 使用 `--xha-*` CSS 变量，父应用统一覆盖
- Element Plus 按需引入（unplugin-vue-components + unplugin-auto-import），直接使用组件和 API 无需手动导入
- 组件内自定义样式使用 `<style scoped>`，引用 `var(--xha-*)` 变量

## Workspace 依赖

- `@hyluo2/spec-config`（workspace:*）— ESLint / Prettier / lint-staged 配置函数
- `@civi/url-plugin`（workspace:*）— 开发代理：`urlPlugin()` 显示多环境地址，`proxyConfig` 按 referer 自动路由
```

## 第三步：生成后提示

文件生成完毕后，输出以下操作指引：

```
项目已生成！请执行以下命令：

cd {{projectName}}
pnpm install     # 安装依赖
pnpm serve       # 启动开发服务器（HTTPS）
```

## Vue 2 → Vue 3 关键 API 对照表

生成代码时遵循以下转换规则：

| Vue 2 | Vue 3 |
|-------|-------|
| `new Vue(...).$mount('#app')` | `createApp(App).mount('#app')` |
| `Vue.use(plugin)` | `app.use(plugin)` |
| `Vue.prototype.$xxx` | `app.config.globalProperties.$xxx` |
| `Vue.set(obj, key, val)` | 直接赋值 `obj[key] = val` |
| `Vue.directive('name', def)` | `app.directive('name', def)` |
| `Vue.filter('name', fn)` | 移除，使用普通函数 |
| `this.$router` / `this.$route` | `useRouter()` / `useRoute()` |
| `new VueRouter({ routes })` | `createRouter({ history: createWebHashHistory(), routes })` |
| 指令 `bind` / `inserted` / `unbind` | `beforeMount` / `mounted` / `unmounted` |
| `import { Message } from 'element-ui'` | 按需自动引入，直接使用 `ElMessage` |

## 技术栈说明

| 层面 | 技术选型 |
|------|---------|
| 语言 | TypeScript（strict 模式） |
| 框架 | Vue 3 + Vue Router 4 |
| UI 库 | Element Plus（按需引入，unplugin-vue-components + unplugin-auto-import） |
| 构建 | Rsbuild（pluginVue + pluginVueJsx + pluginBabel + pluginBasicSsl） |
| 样式 | Tailwind CSS v4（CSS-first，@theme，带项目前缀） |
| Design Token | `--xha-*` 前缀，父应用统一定义 |
| CSS 处理 | @tailwindcss/postcss + postcss-pxtorem |
| 状态管理 | ref/reactive + composable（VueUse） |
| 代码规范 | `@hyluo2/spec-config`（workspace:*）— ESLint + Prettier + lint-staged 配置 |
| 开发代理 | `@civi/url-plugin`（workspace:*）— urlPlugin 显示多环境地址 + proxyConfig 按 referer 自动路由 |
| 包管理 | pnpm |

## 注意事项

### Tailwind 前缀隔离
每个子项目使用独立的 Tailwind 前缀（如 `nw:flex`、`ag:p-4`），防止多子应用在同一页面中工具类命名冲突。

### Design Token 继承
`--xha-*` CSS 变量在非 iframe 模式下通过 DOM 级联自动继承父应用的值。独立运行时使用 `var()` 中的 fallback 默认值。

### @hyluo2/spec-config 使用方式
- 子项目在 devDependencies 中引入 `@hyluo2/spec-config`（workspace:*）
- 在 `.eslintrc.js`、`.prettierrc.js`、`.lintstagedrc.cjs` 中调用配置函数即可
- Git Hooks 和提交校验由 monorepo 根目录统一管理，子项目无需关心
