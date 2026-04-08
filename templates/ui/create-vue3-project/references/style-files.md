# 样式文件模板

本文件包含 Tailwind CSS v4 入口文件和 Element Plus 主题定制的完整模板。

项目不使用 SCSS，所有样式通过 Tailwind CSS v4 + CSS 自定义属性管理。

---

## src/assets/css/tailwind.css

`{{twPrefix}}` 需要替换为项目的 Tailwind 前缀（如 `nw`、`ag`），默认取项目名英文首字母简写。使用时用冒号分隔：`nw:flex`、`nw:p-4`。

```css
/* Tailwind CSS v4 入口 */
/* prefix 为项目独立前缀，防止多子应用工具类污染 */
@import "tailwindcss" prefix({{twPrefix}});

/*
 * Design Token 体系
 *
 * 使用 --xha-* 前缀的 CSS 变量作为 design token。
 * 独立运行时使用 fallback 默认值；作为子应用接入父应用时，
 * 父应用通过覆盖 --xha-* 变量统一所有子应用的视觉风格。
 *
 * 非 iframe 模式：子应用 DOM 在父文档中，CSS 变量自然级联继承。
 * iframe 模式：需通过 micro-app 的 data 通道传递 token 并注入。
 */

/* ========================================
 * Design Token 默认值
 * --xha-* 由父应用统一定义和下发
 * 此处仅提供独立运行时的 fallback 默认值
 * 作为子应用接入时，父应用会覆盖这些变量
 * ======================================== */
:root {
  /* Design Token 默认值（独立运行时生效，父应用会覆盖） */
  --xha-color-primary: #0d1736;
  --xha-color-accent: #3271fa;
  --xha-color-success: #35b55c;
  --xha-color-warning: #ffb526;
  --xha-color-error: #E71111;
  --xha-color-border: #d9dde4;
  --xha-color-text: #262626;
  --xha-color-text-secondary: #8c8c8c;
  --xha-color-bg: #f5f7fa;
  --xha-color-bg-elevated: #ffffff;
  --xha-color-data-1: #3271FA;
  --xha-color-data-2: #56CF73;
  --xha-color-data-3: #FFB526;
  --xha-color-data-4: #FF6B6B;
  --xha-color-data-5: #A05CE6;

  /* Element Plus 主题覆盖 */
  --el-color-primary: var(--xha-color-accent);
  --el-color-success: var(--xha-color-success);
  --el-color-warning: var(--xha-color-warning);
  --el-color-danger: var(--xha-color-error);
  --el-border-color: var(--xha-color-border);
  --el-text-color-primary: var(--xha-color-text);
  --el-text-color-regular: var(--xha-color-text);
  --el-bg-color: var(--xha-color-bg-elevated);
  --el-fill-color-blank: var(--xha-color-bg-elevated);
}

/* ========================================
 * Tailwind 主题配置（CSS-first，替代 tailwind.config.js）
 * 直接引用 --xha-* design token，工具类值跟随父应用动态变化
 * ======================================== */
@theme {
  --color-primary: var(--xha-color-primary);
  --color-accent: var(--xha-color-accent);
  --color-success: var(--xha-color-success);
  --color-warning: var(--xha-color-warning);
  --color-error: var(--xha-color-error);
  --color-border: var(--xha-color-border);
  --color-text: var(--xha-color-text);
  --color-text-secondary: var(--xha-color-text-secondary);
  --color-bg: var(--xha-color-bg);
  --color-bg-elevated: var(--xha-color-bg-elevated);
  --color-data-1: var(--xha-color-data-1);
  --color-data-2: var(--xha-color-data-2);
  --color-data-3: var(--xha-color-data-3);
  --color-data-4: var(--xha-color-data-4);
  --color-data-5: var(--xha-color-data-5);
}

/* ========================================
 * 全局基础样式
 * ======================================== */
@layer base {
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
      'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol';
    color: var(--xha-color-text, #262626);
    background-color: var(--xha-color-bg, #f5f7fa);
  }
}

```

---

## Design Token 使用说明

### 在 Tailwind 工具类中使用（带前缀）

假设项目前缀为 `nw`：

```html
<!-- 使用 @theme 中定义的颜色 -->
<div class="nw:bg-accent nw:text-white nw:p-4">
  按钮
</div>

<!-- 响应式 -->
<div class="nw:flex nw:flex-col md:nw:flex-row">
  内容
</div>
```

### 在组件 `<style>` 中使用

```css
/* 直接使用 --xha-* design token */
.header {
  background-color: var(--xha-color-primary);
  border-bottom: 1px solid var(--xha-color-border);
}
```

### 父应用覆盖 design token

父应用在全局 CSS 中设置 `--xha-*` 变量，所有非 iframe 子应用自动继承：

```css
/* 父应用的全局样式 */
:root {
  --xha-color-primary: #1a2b5e;
  --xha-color-accent: #4080ff;
  --xha-color-border: #e0e0e0;
}
```
