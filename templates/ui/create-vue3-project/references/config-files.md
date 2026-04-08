# 根配置文件模板

模板中 `{{变量名}}` 为需要替换的配置项。

---

## package.json

```json
{
  "name": "{{projectName}}",
  "version": "0.1.0",
  "private": true,
  "packageManager": "pnpm@9.15.0",
  "scripts": {
    "serve": "rsbuild dev",
    "build": "rsbuild build",
    "lint": "eslint --fix --ext .js,.jsx,.ts,.tsx,.vue src/"
  },
  "dependencies": {
    "vue": "^3.5.13",
    "vue-router": "^4.5.0",
    "element-plus": "^2.9.1",
    "@element-plus/icons-vue": "^2.3.1",
    "axios": "^1.7.9",
    "dayjs": "^1.11.13",
    "lodash-es": "^4.17.21",
    "@hyluo2/axios-crypto": "^0.0.4",
    "@vueuse/core": "^12.0.0"
  },
  "devDependencies": {
    "@rsbuild/core": "^1.1.12",
    "@rsbuild/plugin-vue": "^1.0.5",
    "@rsbuild/plugin-vue-jsx": "^1.0.2",
    "@rsbuild/plugin-babel": "^1.0.3",
    "@rsbuild/plugin-basic-ssl": "^1.1.1",
    "typescript": "^5.8.2",
    "tailwindcss": "^4.0.0",
    "@tailwindcss/postcss": "^4.0.0",
    "postcss-pxtorem": "^6.0.0",
    "unplugin-vue-components": "^28.0.0",
    "unplugin-auto-import": "^19.0.0",
    "@civi/url-plugin": "workspace:*",
    "@hyluo2/spec-config": "workspace:*"
  },
  "browserslist": [
    "> 1%",
    "last 2 versions",
    "not dead"
  ]
}
```

说明：
- `@hyluo2/spec-config`（workspace:*）— ESLint / Prettier / lint-staged 配置函数
- `@civi/url-plugin`（workspace:*）— `urlPlugin()` 显示多环境地址 + `proxyConfig` 按 referer 自动路由

---

## rsbuild.config.ts

```ts
import { defineConfig } from '@rsbuild/core'
import { pluginBabel } from '@rsbuild/plugin-babel'
import { pluginBasicSsl } from '@rsbuild/plugin-basic-ssl'
import { pluginVue } from '@rsbuild/plugin-vue'
import { pluginVueJsx } from '@rsbuild/plugin-vue-jsx'
import { proxyConfig, urlPlugin } from '@civi/url-plugin'
import AutoImport from 'unplugin-auto-import/rspack'
import Components from 'unplugin-vue-components/rspack'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  html: {
    template: './public/index.html',
    templateParameters: {
      BASE_URL: '{{assetPrefix}}',
      title: '{{projectTitle}}',
    },
  },
  dev: {
    lazyCompilation: true,
    client: {
      overlay: false,
    },
  },
  plugins: [
    pluginBabel({
      include: /\.(?:jsx|tsx)$/,
    }),
    pluginVue(),
    pluginVueJsx(),
    pluginBasicSsl(),
    urlPlugin(),
  ],
  source: {
    entry: {
      index: './src/main.ts',
    },
    alias: {
      '@': './src',
    },
  },
  server: {
    cors: true,
    https: true,
    allowedHosts: 'all',
    port: {{port}},
    proxy: {
      // 按需配置代理路径，proxyConfig 会根据 referer 自动路由到对应环境
      // '/api': proxyConfig,
    },
  },
  tools: {
    rspack: {
      plugins: [
        AutoImport({
          resolvers: [ElementPlusResolver()],
        }),
        Components({
          resolvers: [ElementPlusResolver()],
        }),
      ],
    },
  },
  performance: {
    removeConsole: ['log', 'warn'],
  },
  output: {
    distPath: { root: '{{outputDir}}' },
    assetPrefix: '{{assetPrefix}}',
    sourceMap: {
      js: process.env.NODE_ENV === 'development' ? 'cheap-module-source-map' : false,
    },
    dataUriLimit: {
      image: 5000,
      media: 0,
    },
  },
})
```

---

## postcss.config.js

```js
module.exports = {
  plugins: {
    '@tailwindcss/postcss': {},
    'postcss-pxtorem': {
      rootValue: 100,
      propList: ['*'],
    },
  },
}
```

---

## .eslintrc.js

使用 `@hyluo2/spec-config` 提供的 Vue 3 + TypeScript ESLint 预设：

```js
const { getEslintConfig } = require('@hyluo2/spec-config')

module.exports = getEslintConfig('vue3-ts')
```

---

## .prettierrc.js

使用 `@hyluo2/spec-config` 提供的 Prettier 预设：

```js
const { getPrettierConfig } = require('@hyluo2/spec-config')

module.exports = getPrettierConfig()
```

---

## .lintstagedrc.cjs

使用 `@hyluo2/spec-config` 提供的 lint-staged 预设，传入预设名自动匹配启用项：

```js
const { getLintStagedConfig } = require('@hyluo2/spec-config')

module.exports = getLintStagedConfig('vue3-ts')
```

---

## .editorconfig

```ini
root = true

[*]
charset = utf-8
indent_style = space
indent_size = 2
end_of_line = lf
trim_trailing_whitespace = true
insert_final_newline = true

[*.md]
max_line_length = off
trim_trailing_whitespace = false
```

---

## tsconfig.json

```json
{
  "include": ["src/**/*.ts", "src/**/*.d.ts", "src/**/*.tsx", "src/**/*.vue"],
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "jsx": "preserve",
    "noEmit": true,
    "isolatedModules": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "resolveJsonModule": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "vueCompilerOptions": {
    "target": 3.5
  }
}
```

---

## .env

```
PORT = {{port}}
```

---

## .gitignore

```
.DS_Store
node_modules
dist
{{outputDir}}

.env.local
.env.*.local
*.local.json

npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*

.idea
.vscode
.history
.claude
*.zip
```

---

## public/index.html

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width,initial-scale=1.0" />
    <link rel="icon" href="<%= BASE_URL %>favicon.ico" />
    <title><%= title %></title>
  </head>
  <body>
    <noscript>
      <strong>请启用 JavaScript 以获得最佳体验。</strong>
    </noscript>
    <div id="app"></div>
  </body>
</html>
```
